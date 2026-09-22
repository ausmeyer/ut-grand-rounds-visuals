// All three pages use the same API. The missing-function fallback keeps existing
// installations usable until the presenter runs polls.sql. It never retries an
// authorization, validation, or network failure through another API.
export async function callPoll(client,poll,name,args={}) {
  const invoke=(fn,body)=>client.rpc(fn,body).abortSignal(AbortSignal.timeout(15000));
  const body=name==='is_presenter'?{}:{p_poll:poll,...args};
  let result=await invoke(`poll_${name}`,body);
  if(result.error?.code==='PGRST202') {
    let legacyName,legacyArgs;
    if(name==='is_presenter') {
      legacyName='poll1_is_presenter';legacyArgs={};
    } else if(poll===1) {
      legacyName=`poll1_${name}`;legacyArgs=args;
      if(name==='submit')legacyArgs={
        p_session:args.p_session,p_week:args.p_start,
        p_unsure:args.p_kind==='not_sure'?true:args.p_kind==='week'?false:null,
      };
    } else {
      legacyName=`poll23_${name}`;legacyArgs=body;
    }
    result=await invoke(legacyName,legacyArgs);
    if(!result.error&&poll===1&&name==='results') {
      const bins=result.data.bins.map(bin=>({value:bin.week,count:bin.count}));
      result.data={bins,numeric_count:bins.reduce((sum,bin)=>sum+bin.count,0),unsure:result.data.unsure};
    }
  }
  if(result.error)throw result.error;
  return result.data;
}
