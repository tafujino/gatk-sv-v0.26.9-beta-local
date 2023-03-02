"use strict";(self.webpackChunkGATK_SV=self.webpackChunkGATK_SV||[]).push([[743],{3905:(e,t,n)=>{n.d(t,{Zo:()=>u,kt:()=>k});var r=n(7294);function i(e,t,n){return t in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function a(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}function l(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?a(Object(n),!0).forEach((function(t){i(e,t,n[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):a(Object(n)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))}))}return e}function o(e,t){if(null==e)return{};var n,r,i=function(e,t){if(null==e)return{};var n,r,i={},a=Object.keys(e);for(r=0;r<a.length;r++)n=a[r],t.indexOf(n)>=0||(i[n]=e[n]);return i}(e,t);if(Object.getOwnPropertySymbols){var a=Object.getOwnPropertySymbols(e);for(r=0;r<a.length;r++)n=a[r],t.indexOf(n)>=0||Object.prototype.propertyIsEnumerable.call(e,n)&&(i[n]=e[n])}return i}var s=r.createContext({}),p=function(e){var t=r.useContext(s),n=t;return e&&(n="function"==typeof e?e(t):l(l({},t),e)),n},u=function(e){var t=p(e.components);return r.createElement(s.Provider,{value:t},e.children)},c="mdxType",d={inlineCode:"code",wrapper:function(e){var t=e.children;return r.createElement(r.Fragment,{},t)}},m=r.forwardRef((function(e,t){var n=e.components,i=e.mdxType,a=e.originalType,s=e.parentName,u=o(e,["components","mdxType","originalType","parentName"]),c=p(n),m=i,k=c["".concat(s,".").concat(m)]||c[m]||d[m]||a;return n?r.createElement(k,l(l({ref:t},u),{},{components:n})):r.createElement(k,l({ref:t},u))}));function k(e,t){var n=arguments,i=t&&t.mdxType;if("string"==typeof e||i){var a=n.length,l=new Array(a);l[0]=m;var o={};for(var s in t)hasOwnProperty.call(t,s)&&(o[s]=t[s]);o.originalType=e,o[c]="string"==typeof e?e:i,l[1]=o;for(var p=2;p<a;p++)l[p]=n[p];return r.createElement.apply(null,l)}return r.createElement.apply(null,n)}m.displayName="MDXCreateElement"},9195:(e,t,n)=>{n.r(t),n.d(t,{assets:()=>s,contentTitle:()=>l,default:()=>d,frontMatter:()=>a,metadata:()=>o,toc:()=>p});var r=n(7462),i=(n(7294),n(3905));const a={title:"Quick Start",description:"Run the pipeline on demo data.",sidebar_position:1,slug:"./qs"},l=void 0,o={unversionedId:"gs/quick_start",id:"gs/quick_start",title:"Quick Start",description:"Run the pipeline on demo data.",source:"@site/docs/gs/quick_start.md",sourceDirName:"gs",slug:"/gs/qs",permalink:"/gatk-sv/docs/gs/qs",draft:!1,editUrl:"https://github.com/broadinstitute/gatk-sv/tree/master/website/docs/gs/quick_start.md",tags:[],version:"current",sidebarPosition:1,frontMatter:{title:"Quick Start",description:"Run the pipeline on demo data.",sidebar_position:1,slug:"./qs"},sidebar:"tutorialSidebar",previous:{title:"Overview",permalink:"/gatk-sv/docs/gs/overview"},next:{title:"Input Data",permalink:"/gatk-sv/docs/gs/inputs"}},s={},p=[{value:"Setup Environment",id:"setup-environment",level:3},{value:"Build Inputs",id:"build-inputs",level:3},{value:"MELT",id:"melt",level:3},{value:"Requester Pays Buckets",id:"requester-pays-buckets",level:3},{value:"Execution",id:"execution",level:3}],u={toc:p},c="wrapper";function d(e){let{components:t,...n}=e;return(0,i.kt)(c,(0,r.Z)({},u,n,{components:t,mdxType:"MDXLayout"}),(0,i.kt)("p",null,"This page provides steps for running the pipeline using demo data."),(0,i.kt)("h1",{id:"quick-start-on-cromwell"},"Quick Start on Cromwell"),(0,i.kt)("p",null,"This section walks you through the steps of running pipeline using\ndemo data on a managed Cromwell server."),(0,i.kt)("h3",{id:"setup-environment"},"Setup Environment"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},"A running instance of a Cromwell server.")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},"Install Cromshell and configure it to connect with the Cromwell server you are using.\nYou may refer to the documentation on ",(0,i.kt)("a",{parentName:"p",href:"https://github.com/broadinstitute/cromshell"},"Cromshell README"),"."))),(0,i.kt)("h3",{id:"build-inputs"},"Build Inputs"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},"Example workflow inputs can be found in ",(0,i.kt)("inlineCode",{parentName:"p"},"/inputs"),".\nBuild using ",(0,i.kt)("inlineCode",{parentName:"p"},"scripts/inputs/build_default_inputs.sh"),",\nwhich generates input jsons in ",(0,i.kt)("inlineCode",{parentName:"p"},"/inputs/build"),".")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("p",{parentName:"li"},"Some workflows require a Google Cloud Project ID to be defined in\na cloud environment parameter group. Workspace builds require a\nTerra billing project ID as well. An example is provided at\n",(0,i.kt)("inlineCode",{parentName:"p"},"/inputs/values/google_cloud.json")," but should not be used,\nas modifying this file will cause tracked changes in the repository.\nInstead, create a copy in the same directory with the format\n",(0,i.kt)("inlineCode",{parentName:"p"},"google_cloud.my_project.json")," and modify as necessary."),(0,i.kt)("p",{parentName:"li"},"Note that these inputs are required only when certain data are\nlocated in requester pays buckets. If this does not apply,\nusers may use placeholder values for the cloud configuration\nand simply delete the inputs manually."))),(0,i.kt)("h3",{id:"melt"},"MELT"),(0,i.kt)("p",null,"Important: The example input files contain MELT inputs that are NOT public\n(see ",(0,i.kt)("a",{parentName:"p",href:"https://github.com/broadinstitute/gatk-sv#requirements"},"Requirements"),"). These include:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"GATKSVPipelineSingleSample.melt_docker")," and ",(0,i.kt)("inlineCode",{parentName:"li"},"GATKSVPipelineBatch.melt_docker")," - MELT docker URI\n(see ",(0,i.kt)("a",{parentName:"li",href:"https://github.com/talkowski-lab/gatk-sv-v1/blob/master/dockerfiles/README.md"},"Docker readme"),")"),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"GATKSVPipelineSingleSample.ref_std_melt_vcfs")," - Standardized MELT VCFs (",(0,i.kt)("a",{parentName:"li",href:"/docs/modules/gbe"},"GatherBatchEvidence"),")\nThe input values are provided only as an example and are not publicly accessible. "),(0,i.kt)("li",{parentName:"ul"},"In order to include MELT, these values must be provided by the user. MELT can be\ndisabled by deleting these inputs and setting ",(0,i.kt)("inlineCode",{parentName:"li"},"GATKSVPipelineBatch.use_melt")," to false.")),(0,i.kt)("h3",{id:"requester-pays-buckets"},"Requester Pays Buckets"),(0,i.kt)("p",null,"The following parameters must be set when certain input data is in requester pays (RP) buckets:"),(0,i.kt)("p",null,(0,i.kt)("inlineCode",{parentName:"p"},"GATKSVPipelineSingleSample.requester_pays_cram")," and\n",(0,i.kt)("inlineCode",{parentName:"p"},"GATKSVPipelineBatch.GatherSampleEvidenceBatch.requester_pays_crams")," -\nset to ",(0,i.kt)("inlineCode",{parentName:"p"},"True")," if inputs are CRAM format and in an RP bucket, otherwise ",(0,i.kt)("inlineCode",{parentName:"p"},"False"),"."),(0,i.kt)("h3",{id:"execution"},"Execution"),(0,i.kt)("pre",null,(0,i.kt)("code",{parentName:"pre",className:"language-shell"},'> mkdir gatksv_run && cd gatksv_run\n> mkdir wdl && cd wdl\n> cp $GATK_SV_ROOT/wdl/*.wdl .\n> zip dep.zip *.wdl\n> cd ..\n> echo \'{ "google_project_id": "my-google-project-id", "terra_billing_project_id": "my-terra-billing-project" }\' > inputs/values/google_cloud.my_project.json\n> bash scripts/inputs/build_default_inputs.sh -d $GATK_SV_ROOT -c google_cloud.my_project\n> cp $GATK_SV_ROOT/inputs/build/ref_panel_1kg/test/GATKSVPipelineBatch/GATKSVPipelineBatch.json GATKSVPipelineBatch.my_run.json\n> cromshell submit wdl/GATKSVPipelineBatch.wdl GATKSVPipelineBatch.my_run.json cromwell_config.json wdl/dep.zip\n')),(0,i.kt)("p",null,"where ",(0,i.kt)("inlineCode",{parentName:"p"},"cromwell_config.json")," is a Cromwell\n",(0,i.kt)("a",{parentName:"p",href:"https://cromwell.readthedocs.io/en/stable/wf_options/Overview/"},"workflow options file"),".\nNote users will need to re-populate batch/sample-specific parameters (e.g. BAMs and sample IDs)."))}d.isMDXComponent=!0}}]);