#!/usr/bin/env python

import attr
import sys
from pathlib import Path
import tempfile
import argparse
import warnings
from tqdm.auto import tqdm as tqdm
import numpy.random
import pandas.core.arrays
import torch
import concurrent.futures

from sv_utils import common
from gq_recalibrator import (
    tarred_properties_to_parquet, vcf_training_data_loader, training_utils, gq_recalibrator_net
)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import dask.dataframe
from types import MappingProxyType
from typing import Optional, Union, Any
from collections.abc import Mapping

tqdm.monitor_interval = 0

DaskDataFrame = dask.dataframe.DataFrame
PandasDataFrame = pandas.DataFrame
DataFrame = Union[DaskDataFrame, PandasDataFrame]
ArrowStringArray = pandas.core.arrays.string_arrow.ArrowStringArray


class Keys:
    id = tarred_properties_to_parquet.Keys.id
    variant_weights = tarred_properties_to_parquet.Keys.variant_weights
    positive_value = tarred_properties_to_parquet.Keys.positive_value
    negative_value = tarred_properties_to_parquet.Keys.negative_value
    baseline = tarred_properties_to_parquet.Keys.baseline
    scale = tarred_properties_to_parquet.Keys.scale
    logger_kwargs = "logger_kwargs"
    data_loader_state = "data_loader_state"
    properties_scaling = "properties_scaling"
    properties_summary = "properties_summary"
    net_kwargs = "neural_net_kwargs"
    optimizer_kwargs = "optimizer_kwargs"
    optimizer_type = "optimizer_type"
    training_losses = "training_losses"
    training_truth_agreement_losses = "training_truth_agreement_losses"
    training_gq_correlations = "training_gq_correlations"
    validation_losses = "validation_losses"
    validation_truth_agreement_losses = "validation_truth_agreement_losses"
    validation_gq_correlations = "validation_gq_correlations"


class Default:
    temp_dir = Path(tempfile.gettempdir())
    variants_per_batch = 100
    batches_per_mini_epoch = 50
    shuffle = vcf_training_data_loader.Default.shuffle
    random_state = vcf_training_data_loader.Default.random_seed
    non_filtration_properties = vcf_training_data_loader.Default.non_filtration_properties
    torch_device_kind = training_utils.TorchDeviceKind.cpu
    scale_bool_properties = vcf_training_data_loader.Default.scale_bool_properties
    validation_proportion = vcf_training_data_loader.Default.validation_proportion
    num_hidden_layers = gq_recalibrator_net.Default.num_hidden_layers
    layer_expansion_factor = gq_recalibrator_net.Default.layer_expansion_factor
    bias = gq_recalibrator_net.Default.bias
    optim_type = torch.optim.AdamW
    optim_kwargs = MappingProxyType({"weight_decay": 0, "lr": 1.0e-3})
    hidden_nonlinearity = gq_recalibrator_net.Default.hidden_nonlinearity
    output_nonlinearity = gq_recalibrator_net.Default.output_nonlinearity
    max_gradient_value = 1.0e-2
    max_gradient_norm = 1.0e-2
    correlation_loss_weight = 0.5
    max_look_ahead_batches = vcf_training_data_loader.Default.max_look_ahead_batches
    num_processes = vcf_training_data_loader.Default.max_look_ahead_batches + 1
    keep_multiallelic = True
    keep_homref = False
    keep_homvar = False


def __parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train filter to recalibrate genotype quality from extracted VCF properties",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog=argv[0]
    )
    parser.add_argument("--properties", "-p", type=Path, required=True,
                        help="full path to tarred parquet file with variant properties")
    parser.add_argument(
        "--truth-json", type=Path, required=True,
        help="full path to JSON with info about which GTs are good for each variant x sample"
    )
    parser.add_argument("--model", "-m", type=Path, required=True,
                        help="path to output file with trained model")
    parser.add_argument("--input-model", "-i", type=Path, required=False,
                        help="path to input file with partially trained model. If not specified or"
                             " a file doesn't exist at the path, training will start from scratch")
    parser.add_argument("--keep-multiallelic", type=bool, default=Default.keep_multiallelic,
                        help="If True, do not train on multiallelic variants; if False, do so")
    parser.add_argument("--keep-homref", type=bool, default=Default.keep_homref,
                        help="If True, treat all HOMREF genotypes as good/correct for training, as"
                             f"though they were specified in the truth json; if False, train on "
                             f"HOMREF genotypes as usual.")
    parser.add_argument("--keep-homvar", type=bool, default=Default.keep_homvar,
                        help="If True, treat all HOMVAR genotypes as good/correct for training, as"
                             f"though they were specified in the truth json; if False, train on "
                             f"HOMVAR genotypes as usual.")
    parser.add_argument("--variants-per-batch", type=int, default=Default.variants_per_batch,
                        help="number of variants used in each training batch")
    parser.add_argument("--batches-per-mini-epoch", type=int,
                        default=Default.batches_per_mini_epoch,
                        help="number of batches between progress updates and checkpoints")
    parser.add_argument("--max-train-variants", type=int, default=None,
                        help="maximum number of variants to train before ending training")
    parser.add_argument("--temp-dir", type=Path, default=Default.temp_dir,
                        help="preferred path to folder for temporary files")
    parser.add_argument("--shuffle", type=common.argparse_bool, default=Default.shuffle,
                        help="if True, shuffle order of variants while training")
    parser.add_argument("--random-seed", type=int, default=Default.random_state,
                        help="initial random seed")
    parser.add_argument(
        "--excluded-properties", type=str, default=','.join(Default.non_filtration_properties),
        help="comma-separated list of additional properties to not use in training or filtering. "
             f"Default excluded properties cannot be used (will remain excluded), passing"
             f"--exclude-properties will add one or more properties to exclude."
    )
    # noinspection PyTypeChecker
    parser.add_argument(
        "--torch-device", type=str, default=Default.torch_device_kind,
        choices=training_utils.TorchDeviceKind.choices,
        help="Device on which to perform training"
    )
    parser.add_argument(
        "--scale-bool-properties", type=common.argparse_bool,
        default=Default.scale_bool_properties,
        help="If true, z-score bool variables too. If false, leave as 0.0 or 1.0. Scaling can "
             "result in large values if the bool variable is mostly true or mostly false."
    )
    parser.add_argument(
        "--num-processes", type=int, default=Default.num_processes,
        help="Number of cpu processes to use. One for training, the rest for loading data."
    )
    return parser.parse_args(argv[1:] if len(argv) > 1 else ["--help"])


def main(argv: Optional[list[str]] = None):
    args = __parse_arguments(sys.argv if argv is None else argv)
    train_sv_gq_recalibrator(
        properties_path=args.properties,
        truth_json=args.truth_json,
        output_model_path=args.model,
        input_model_path=args.input_model,
        temp_dir=args.temp_dir,
        keep_multiallelic=args.keep_multiallelic,
        keep_homref=args.keep_homref,
        keep_homvar=args.keep_homvar,
        variants_per_batch=args.variants_per_batch,
        batches_per_mini_epoch=args.batches_per_mini_epoch,
        max_train_variants=args.max_train_variants,
        shuffle=args.shuffle,
        random_state=args.random_seed,
        excluded_properties=set(args.excluded_properties.split(',')),
        torch_device_kind=training_utils.TorchDeviceKind(args.torch_device),
        num_processes=args.num_processes
    )


def train_sv_gq_recalibrator(
        properties_path: Path,
        truth_json: Path,
        output_model_path: Path,
        input_model_path: Optional[Path] = None,
        temp_dir: Path = Default.temp_dir,
        keep_multiallelic: bool = Default.keep_multiallelic,
        keep_homref: bool = Default.keep_homref,
        keep_homvar: bool = Default.keep_homvar,
        variants_per_batch: int = Default.variants_per_batch,
        batches_per_mini_epoch: int = Default.batches_per_mini_epoch,
        max_train_variants: Optional[int] = None,
        shuffle: bool = Default.shuffle,
        random_state: Union[int, numpy.random.RandomState, None] = Default.random_state,
        excluded_properties: set[str] = frozenset({}),
        torch_device_kind: training_utils.TorchDeviceKind = Default.torch_device_kind,
        scale_bool_values: bool = Default.scale_bool_properties,
        num_hidden_layers: int = Default.num_hidden_layers,
        layer_expansion_factor: float = Default.layer_expansion_factor,
        bias: bool = Default.bias,
        optim_type: type = Default.optim_type,
        optim_kwargs: Mapping[str, Any] = Default.optim_kwargs,
        hidden_nonlinearity: torch.nn.Module = Default.hidden_nonlinearity,
        output_nonlinearity: torch.nn.Module = Default.output_nonlinearity,
        max_gradient_value: Optional[float] = Default.max_gradient_value,
        max_gradient_norm: Optional[float] = Default.max_gradient_norm,
        correlation_loss_weight: float = Default.correlation_loss_weight,
        max_look_ahead_batches: int = Default.max_look_ahead_batches,
        num_processes: int = Default.num_processes
):
    variants_trained = 0
    non_filtration_properties = Default.non_filtration_properties.union(excluded_properties)
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as process_executor:
        # create the tensor data loader
        if input_model_path is None or not input_model_path.is_file():
            training_state = TrainingState.build(
                process_executor=process_executor, properties_path=properties_path,
                truth_json=truth_json,
                temp_dir=temp_dir,
                keep_multiallelic=keep_multiallelic, keep_homref=keep_homref,
                keep_homvar=keep_homvar,
                variants_per_batch=variants_per_batch, shuffle=shuffle, random_state=random_state,
                non_filtration_properties=non_filtration_properties,
                torch_device_kind=torch_device_kind, scale_bool_values=scale_bool_values,
                num_hidden_layers=num_hidden_layers, layer_expansion_factor=layer_expansion_factor,
                bias=bias, optim_type=optim_type, optim_kwargs=optim_kwargs,
                hidden_nonlinearity=hidden_nonlinearity, output_nonlinearity=output_nonlinearity,
                max_look_ahead_batches=max_look_ahead_batches
            )
        else:
            training_state = TrainingState.load(
                save_path=input_model_path, process_executor=process_executor,
                parquet_path=properties_path,
                temp_dir=temp_dir,
                keep_multiallelic=keep_multiallelic, keep_homref=keep_homref,
                keep_homvar=keep_homvar,
                truth_json=truth_json, variants_per_batch=variants_per_batch, shuffle=shuffle,
                non_filtration_properties=non_filtration_properties,
                torch_device_kind=torch_device_kind, scale_bool_values=scale_bool_values,
                max_look_ahead_batches=max_look_ahead_batches
            )

        for (is_training_batch, batch_tensor, batch_weights, scaled_gq, is_good_gt, is_bad_gt) in \
                training_state.vcf_tensor_data_loader:
            if is_training_batch:
                training_state.optimizer.zero_grad()
                predicted_probabilities = training_state.gq_recalibrator(batch_tensor)
                loss, truth_agreement_loss, gq_correlation = loss_function(
                    predicted_probabilities=predicted_probabilities, variant_weights=batch_weights,
                    scaled_gq_values=scaled_gq, genotype_is_good=is_good_gt,
                    genotype_is_bad=is_bad_gt, correlation_loss_scale=correlation_loss_weight
                )
                loss.backward()
                if max_gradient_value is not None:
                    torch.nn.utils.clip_grad_value_(
                        training_state.gq_recalibrator.parameters(), max_gradient_value
                    )
                if max_gradient_norm is not None:
                    torch.nn.utils.clip_grad_norm_(
                        training_state.gq_recalibrator.parameters(), max_gradient_norm
                    )
                training_state.optimizer.step()

                training_state.append_loss(
                    training=True, loss=loss, truth_agreement_loss=truth_agreement_loss,
                    correlation=gq_correlation
                )
                variants_trained += variants_per_batch
                if training_state.training_losses.num_mini_epoch_batches >= batches_per_mini_epoch:
                    # log progress summary and save
                    training_state.summarize_training_progress()
                    training_state.training_losses.next_mini_epoch()
                    training_state.validation_losses.next_mini_epoch()
                    training_state.save(save_path=output_model_path)

                if max_train_variants is not None and variants_trained >= max_train_variants:
                    break
            else:
                with torch.no_grad():
                    predicted_probabilities = training_state.gq_recalibrator(batch_tensor)
                    loss, truth_agreement_loss, gq_correlation = loss_function(
                            predicted_probabilities=predicted_probabilities,
                            variant_weights=batch_weights, scaled_gq_values=scaled_gq,
                            genotype_is_good=is_good_gt, genotype_is_bad=is_bad_gt,
                            correlation_loss_scale=correlation_loss_weight
                        )
                    training_state.append_loss(
                        training=False, loss=loss, truth_agreement_loss=truth_agreement_loss,
                        correlation=gq_correlation
                    )

    training_state.summarize_training_progress()
    training_state.save(save_path=output_model_path)

    if torch_device_kind == training_utils.TorchDeviceKind.cuda:
        torch.cuda.empty_cache()

    training_state.summarize_batches_processed()


@attr.define(slots=True, frozen=True)
class TrainingState:
    """ Class to store, init, save, and resume state of objects needed for training """
    training_logger: training_utils.ProgressLogger
    vcf_tensor_data_loader: vcf_training_data_loader.VcfTrainingTensorDataLoader
    properties_summary: tarred_properties_to_parquet.PropertiesSummary
    properties_scaling: tarred_properties_to_parquet.PropertiesScaling
    gq_recalibrator: gq_recalibrator_net.GqRecalibratorNet
    optimizer: Default.optim_type
    training_losses: training_utils.BatchLosses
    training_truth_agreement_losses: training_utils.BatchLosses
    training_gq_correlations: training_utils.BatchLosses
    validation_losses: training_utils.BatchLosses
    validation_truth_agreement_losses: training_utils.BatchLosses
    validation_gq_correlations: training_utils.BatchLosses

    @staticmethod
    def build(
            process_executor: concurrent.futures.ProcessPoolExecutor,
            properties_path: Path,
            truth_json: Path,
            temp_dir: Path,
            keep_multiallelic: bool = Default.keep_multiallelic,
            keep_homref: bool = Default.keep_homref,
            keep_homvar: bool = Default.keep_homvar,
            variants_per_batch: int = Default.variants_per_batch,
            shuffle: bool = Default.shuffle,
            random_state: Union[int, numpy.random.RandomState, None] = Default.random_state,
            non_filtration_properties: set[str] = Default.non_filtration_properties,
            torch_device_kind: training_utils.TorchDeviceKind = Default.torch_device_kind,
            scale_bool_values: bool = Default.scale_bool_properties,
            num_hidden_layers: int = Default.num_hidden_layers,
            layer_expansion_factor: float = Default.layer_expansion_factor,
            bias: bool = Default.bias,
            optim_type: type = Default.optim_type,
            optim_kwargs: Mapping[str, Any] = Default.optim_kwargs,
            hidden_nonlinearity: torch.nn.Module = Default.hidden_nonlinearity,
            output_nonlinearity: torch.nn.Module = Default.output_nonlinearity,
            max_look_ahead_batches: int = Default.max_look_ahead_batches
    ) -> "TrainingState":
        training_logger = training_utils.ProgressLogger()
        vcf_tensor_data_loader = vcf_training_data_loader.VcfTrainingTensorDataLoader(
            parquet_path=properties_path,
            truth_json=truth_json, scale_bool_values=scale_bool_values,
            keep_multiallelic=keep_multiallelic, keep_homref=keep_homref, keep_homvar=keep_homvar,
            variants_per_batch=variants_per_batch, shuffle=shuffle,
            random_generator=random_state, non_filtration_properties=non_filtration_properties,
            torch_device_kind=torch_device_kind, progress_logger=training_logger,
            temp_dir=temp_dir,
            process_executor=process_executor, max_look_ahead_batches=max_look_ahead_batches
        )
        training_logger(
            f"training len: {len(vcf_tensor_data_loader)}\n"
            f"num_samples: {vcf_tensor_data_loader.num_samples}\n"
            f"num_properties: {vcf_tensor_data_loader.num_properties}"
        )
        # create the neural net, move to requested device, and set to train
        gq_recalibrator = gq_recalibrator_net.GqRecalibratorNet(
            num_input_properties=vcf_tensor_data_loader.num_properties,
            num_hidden_layers=num_hidden_layers, layer_expansion_factor=layer_expansion_factor,
            bias=bias, hidden_nonlinearity=hidden_nonlinearity,
            output_nonlinearity=output_nonlinearity,
        ).to(vcf_tensor_data_loader.torch_device).train()
        return TrainingState(
            training_logger=training_logger, vcf_tensor_data_loader=vcf_tensor_data_loader,
            properties_summary=vcf_tensor_data_loader.properties_summary,
            properties_scaling=vcf_tensor_data_loader.properties_scaling,
            gq_recalibrator=gq_recalibrator,
            optimizer=optim_type(gq_recalibrator.parameters(), **optim_kwargs),
            training_losses=training_utils.BatchLosses(),
            training_truth_agreement_losses=training_utils.BatchLosses(),
            training_gq_correlations=training_utils.BatchLosses(),
            validation_losses=training_utils.BatchLosses(),
            validation_truth_agreement_losses=training_utils.BatchLosses(),
            validation_gq_correlations=training_utils.BatchLosses()
        )

    @staticmethod
    def load(
            save_path: Path,
            process_executor: concurrent.futures.ProcessPoolExecutor,
            parquet_path: Path,
            truth_json: Path,
            temp_dir: Path,
            keep_multiallelic: bool = Default.keep_multiallelic,
            keep_homref: bool = Default.keep_homref,
            keep_homvar: bool = Default.keep_homvar,
            variants_per_batch: int = Default.variants_per_batch,
            shuffle: bool = Default.shuffle,
            non_filtration_properties: set[str] = Default.non_filtration_properties,
            torch_device_kind: training_utils.TorchDeviceKind = Default.torch_device_kind,
            scale_bool_values: bool = Default.scale_bool_properties,
            max_look_ahead_batches: int = Default.max_look_ahead_batches
    ) -> "TrainingState":
        with open(save_path, "rb") as f_in:
            pickle_dict = torch.load(f_in)

        # load previous logs
        training_logger = training_utils.ProgressLogger(**pickle_dict[Keys.logger_kwargs])
        training_logger.replay()  # print out the logs from the previous run(s)
        # init
        vcf_tensor_data_loader = vcf_training_data_loader.VcfTrainingTensorDataLoader(
            parquet_path=parquet_path,
            truth_json=truth_json, scale_bool_values=scale_bool_values,
            keep_multiallelic=keep_multiallelic, keep_homref=keep_homref, keep_homvar=keep_homvar,
            variants_per_batch=variants_per_batch, shuffle=shuffle, random_generator=0,
            non_filtration_properties=non_filtration_properties,
            torch_device_kind=torch_device_kind, progress_logger=training_logger,
            temp_dir=temp_dir,
            process_executor=process_executor, max_look_ahead_batches=max_look_ahead_batches,
            **pickle_dict[Keys.data_loader_state]
        )

        # load gq recalibrator
        gq_recalibrator = gq_recalibrator_net.GqRecalibratorNet(**pickle_dict[Keys.net_kwargs])\
            .to(vcf_tensor_data_loader.torch_device).train()
        # load optimizer and connect it to gq_recalibrator paramters:
        optimizer: Keys.optimizer_type = \
            pickle_dict[Keys.optimizer_type](gq_recalibrator.parameters())
        optimizer.load_state_dict(
            TrainingState._state_dict_to(
                state_dict=pickle_dict[Keys.optimizer_kwargs],
                device=vcf_tensor_data_loader.torch_device
            )
        )
        return TrainingState(
            training_logger=training_logger, vcf_tensor_data_loader=vcf_tensor_data_loader,
            properties_summary=pickle_dict[Keys.properties_summary],
            properties_scaling=pickle_dict[Keys.properties_scaling],
            gq_recalibrator=gq_recalibrator,
            optimizer=optimizer,
            training_losses=training_utils.BatchLosses(**pickle_dict[Keys.training_losses]),
            training_truth_agreement_losses=training_utils.BatchLosses(
                **pickle_dict[Keys.training_truth_agreement_losses]
            ),
            training_gq_correlations=training_utils.BatchLosses(
                **pickle_dict[Keys.training_gq_correlations]
            ),
            validation_losses=training_utils.BatchLosses(**pickle_dict[Keys.validation_losses]),
            validation_truth_agreement_losses=training_utils.BatchLosses(
                **pickle_dict[Keys.validation_truth_agreement_losses]
            ),
            validation_gq_correlations=training_utils.BatchLosses(
                **pickle_dict[Keys.validation_gq_correlations]
            )
        )

    @staticmethod
    def _state_dict_to(state_dict: dict[str, Any], device: torch.device) -> dict[str, Any]:
        """
        move state_dict to desired device, necessary for optimizer
        idea taken from: https://discuss.pytorch.org/t/moving-optimizer-from-cpu-to-gpu/96068/3
        """
        moved_state_dict = {}
        for key, param in state_dict.items():
            if isinstance(param, torch.Tensor):
                moved_param = param.detach().to(device)
                # noinspection PyProtectedMember
                if param._grad is not None:
                    # noinspection PyProtectedMember
                    moved_param._grad.data = param.detach()._grad.data.to(device)
                moved_state_dict[key] = moved_param
            elif isinstance(param, dict):
                moved_state_dict[key] = TrainingState._state_dict_to(param, device)
            else:
                moved_state_dict[key] = param
        return moved_state_dict

    def save(self, save_path: Path):
        """ Save neural net and state info for resuming training (or for filtering) """
        save_path.parent.mkdir(parents=True, exist_ok=True)
        cpu_torch_device = training_utils.TorchDeviceKind.cpu.get_device(progress_logger=None)
        pickle_dict = {
            Keys.logger_kwargs: self.training_logger.save_dict,
            Keys.data_loader_state: self.vcf_tensor_data_loader.state_dict,
            Keys.properties_summary: self.properties_summary,
            Keys.properties_scaling: self.properties_scaling,
            Keys.net_kwargs: self.gq_recalibrator.to(cpu_torch_device).save_dict,
            Keys.optimizer_type: type(self.optimizer),
            Keys.optimizer_kwargs: TrainingState._state_dict_to(
                state_dict=self.optimizer.state_dict(), device=cpu_torch_device
            ),
            Keys.training_losses: self.training_losses.save_dict,
            Keys.training_truth_agreement_losses: self.training_truth_agreement_losses.save_dict,
            Keys.training_gq_correlations: self.training_gq_correlations.save_dict,
            Keys.validation_losses: self.validation_losses.save_dict,
            Keys.validation_truth_agreement_losses:
                self.validation_truth_agreement_losses.save_dict,
            Keys.validation_gq_correlations: self.validation_gq_correlations.save_dict
        }
        with open(save_path, "wb") as f_out:
            torch.save(pickle_dict, f_out)

    def append_loss(
        self, training: bool, loss: torch.Tensor, truth_agreement_loss: float, correlation: float
    ):
        if training:
            self.training_losses.append(loss.item())
            self.training_truth_agreement_losses.append(truth_agreement_loss)
            self.training_gq_correlations.append(correlation)
        else:
            self.validation_losses.append(loss.item())
            self.validation_truth_agreement_losses.append(loss.item())
            self.validation_gq_correlations.append(loss.item())

    def summarize_training_progress(self):
        self.training_logger.summarize_training_progress(
            training_losses=self.training_losses,
            training_truth_agreement_losses=self.training_truth_agreement_losses,
            training_gq_correlations=self.training_gq_correlations,
            validation_losses=self.validation_losses,
            validation_truth_agreement_losses=self.validation_truth_agreement_losses,
            validation_gq_correlations=self.validation_gq_correlations
        )

    def summarize_batches_processed(self):
        self.training_logger.log(
            f"Got {len(self.training_losses)} training batches and {len(self.validation_losses)} "
            f"validation batches in {self.training_logger.elapsed_time}"
        )


def loss_function(
        predicted_probabilities: torch.Tensor,
        variant_weights: torch.Tensor,
        genotype_is_good: torch.Tensor,
        genotype_is_bad: torch.Tensor,
        correlation_loss_scale: float,
        scaled_gq_values: torch.Tensor,
) -> tuple[torch.Tensor, float, float]:
    """
    Compute differentiable loss for predicted_probabilities
        predicted_probabilities: num_variants x num_samples tensor
            probabilities each genotype is good, predicted by the neural net
        variant_weights: num_variants-length tensor
            relative importance / weight of each variant for training
        genotype_is_good: torch.Tensor,
        genotype_is_bad: torch.Tensor,
        correlation_loss_scale: float,
        gq_values: num_variants x num_samples tensor
            gq_values, scaled to be nominally close to zero, typically in [-1, 1]
    Args:

    """
    truth_agreement_loss = get_truth_agreement_loss(
        genotype_is_good=genotype_is_good, genotype_is_bad=genotype_is_bad,
        predicted_probabilities=predicted_probabilities, variant_weights=variant_weights
    )
    gq_correlation = get_correlation_coefficient(
        scaled_target_values=scaled_gq_values, predicted_values=predicted_probabilities,
        variant_weights=variant_weights
    )
    loss = truth_agreement_loss + correlation_loss_scale * (1.0 - gq_correlation)
    return loss, truth_agreement_loss.item(), gq_correlation.item()


def get_truth_agreement_loss(
        genotype_is_good: torch.Tensor,
        genotype_is_bad: torch.Tensor,
        predicted_probabilities: torch.Tensor,
        variant_weights: torch.Tensor
) -> torch.Tensor:
    """
    Differentiable strength of agreement between probabilities and truth
    Args:
        genotype_is_good:
        genotype_is_bad:
        predicted_probabilities:
        variant_weights:

    Returns:
    """
    # logically the formula is:
    # genotype_loss = genotype_is_good * (1.0 - predicted_probabilities)
    #               + genotype_is_bad * predicted_probabilities
    # compute this mathematically-equivalent way to get fewer operations and better float accuracy:
    genotype_loss = (
        predicted_probabilities * (genotype_is_bad - genotype_is_good)
        + genotype_is_good
    )
    # compute variant_loss in range [0, 1] by summing genotype_losses over each variant and
    # dividing by maximum score
    variant_loss = genotype_loss.sum(dim=1) / (
            genotype_is_good.sum(dim=1) + genotype_is_bad.sum(dim=1)
    )
    # compute overall loss as mean of weighted variant_loss
    return (variant_loss * variant_weights).mean()


def get_correlation_coefficient(
        scaled_target_values: torch.Tensor,
        predicted_values: torch.Tensor,
        variant_weights: torch.Tensor
) -> torch.Tensor:
    """ Differentiable correlation coefficient between predicted and target values """
    # np.corrcoef in torch from @mdo
    # https://forum.numer.ai/t/custom-loss-functions-for-xgboost-using-pytorch/960
    # adjust probabilities: subtract mean and divide by norm
    predicted_values = 2.0 * (predicted_values - 0.5)
    # noinspection PyUnresolvedReferences
    variant_correlation = (predicted_values * scaled_target_values).mean(dim=1)
    return (variant_correlation * variant_weights).mean()


if __name__ == "__main__":
    main()
