export { isSession } from '../poll-01/model.js';

export const POLLS = Object.freeze({
  2: Object.freeze({
    id:2, kind:'weeks', values:Object.freeze([0,1,2,3,4]),
    question:'How far in advance can we accurately predict the inflection at the peak with quantitative forecasts?',
    instruction:'Choose one answer, then submit.',
    title:'Predicting the inflection at the peak',
    xLabel:'Number of responses', yLabel:'Weeks in advance',
  }),
  3: Object.freeze({
    id:3, kind:'window', values:Object.freeze(Array.from({length:52},(_,i)=>i+1)),
    question:'What time window would you recommend for a typical adult patient to get their annual flu vaccine?',
    instruction:'Choose the first and last week of your preferred window, then submit.',
    title:'Recommended vaccination windows',
    xLabel:'Week of the year', yLabel:'Responses including this week',
  }),
});

export function includesWeek(start,end,week) {
  return start<=end ? week>=start&&week<=end : week>=start||week<=end;
}
export function validAnswer(poll,{kind,start,end}) {
  if(poll.id===3&&kind==='not_sure')return start===null&&end===null;
  if(kind!==poll.kind||!Number.isInteger(start)||!poll.values.includes(start))return false;
  return poll.id===2 ? end===null : Number.isInteger(end)&&poll.values.includes(end);
}
export function normalizeResults(poll,data) {
  const validCount=value=>Number.isSafeInteger(value)&&value>=0;
  if(!data||!Array.isArray(data.bins)||data.bins.length!==poll.values.length||
      !validCount(data.numeric_count)||!validCount(data.unsure)||
      (poll.id===2&&data.unsure!==0))throw new Error('Invalid poll results');
  const bins=poll.values.map((value,i)=>{
    const bin=data.bins[i];
    if(bin?.value!==value||!validCount(bin.count)||bin.count>data.numeric_count)throw new Error('Invalid histogram bin');
    return {value,count:bin.count};
  });
  const total=bins.reduce((sum,bin)=>sum+bin.count,0);
  if(poll.id===2 ? total!==data.numeric_count : total<data.numeric_count)throw new Error('Invalid response counts');
  return {bins,numericCount:data.numeric_count,unsure:data.unsure};
}
// Synthetic illustrations used only in visibly labeled, network-free previews.
export function previewResults(poll) {
  const answers=poll.id===2?[0,1,1,1,2,2,2,2,3,3,4]:[[32,38],[36,42],[38,44],[40,48],[50,3]];
  return {
    bins:poll.values.map(value=>({value,count:answers.filter(answer=>poll.id===2?answer===value:includesWeek(...answer,value)).length})),
    numeric_count:answers.length,unsure:poll.id===3?2:0,
  };
}
