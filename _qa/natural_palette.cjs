
// C / Japanese natural select-shop palette. Transform color values only.
// Preserve alpha, relative luminance, geometry, motion and all content.
const exact={
 "fcfaf7":"f4f1e9","fcfaf8":"f4f1e9","f7f5f0":"f4f1e9","fffaf8":"fdfbf6","fffaf7":"fdfbf6","fffdfa":"fdfbf6","fffdfb":"fdfbf6","fffefd":"fdfbf6","fffcfa":"fdfbf6","fffaf4":"fdfbf6","fffaf5":"fdfbf6",
 "49363e":"403c34","493948":"403c34","57313f":"435247","603d52":"435247","503044":"35463b","56384b":"403c34","563b4c":"403c34","765969":"62564d","795466":"62564d","765267":"62564d","654753":"435247","885365":"536457","785366":"536457","a2647a":"647763","9c637b":"536457","956078":"536457","985773":"536457","d496ad":"b9a58c","e9c6d3":"d9e1d5","f8ebf0":"e6dfd1","edf3eb":"d9e1d5","f1eef6":"e9e3d9","d6b7c7":"bdb5a6","e8d7dd":"d7cfc1","d9c0cb":"bdb5a6",
 "bd8294":"536457","e9c85f":"b4a06d","87a8bd":"8c9d91","9cac92":"a9b396","a6a2bd":"9a8878","a18db1":"9a8878","d9cfd2":"d8cfc0",
 "64364d":"403c34","824660":"536457","ffd2e2":"d9e1d5","fbd5e5":"d9e1d5","a36883":"536457","9a5279":"62564d",
 "fff2e6":"fdfbf6","f4cfe0":"e6dfd1","e4d9f8":"d9e1d5","f9d6e7":"e0cdb4",
 "06c755":"06c755","00b900":"00b900","107c41":"107c41"
};
function rgbHex(r){return r.map(v=>Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,"0")).join("")}
function luma(rgb){return rgb.reduce((a,v,i)=>{let x=v/255;return a+[.2126,.7152,.0722][i]*(x<=.04045?x/12.92:((x+.055)/1.055)**2.4)},0)}
function hsl(rgb){let [r,g,b]=rgb.map(x=>x/255),max=Math.max(r,g,b),min=Math.min(r,g,b),d=max-min,l=(max+min)/2,h=0,s=d===0?0:d/(1-Math.abs(2*l-1));if(d){h=max===r?((g-b)/d+6)%6:max===g?(b-r)/d+2:(r-g)/d+4;h*=60}return [h,s,l]}
function fromHsl(h,s,l){const c=(1-Math.abs(2*l-1))*s,x=c*(1-Math.abs((h/60)%2-1)),m=l-c/2;const a=h<60?[c,x,0]:h<120?[x,c,0]:h<180?[0,c,x]:h<240?[0,x,c]:h<300?[x,0,c]:[c,0,x];return a.map(v=>(v+m)*255)}
function mapRGB(rgb){
 let k=rgbHex(rgb);if(exact[k])return exact[k].match(/../g).map(x=>parseInt(x,16));
 if(k==="ffffff"||k==="000000"||Math.max(...rgb)-Math.min(...rgb)<5)return rgb;
 const [h,s,l]=hsl(rgb);let hue,sat;
 if(h>=285||h<18){hue= l>.72?105:125;sat=l>.82?.16:.14;}
 else if(h<75){hue=38;sat=.23;}
 else if(h<165){hue=105;sat=.15;}
 else if(h<245){hue=145;sat=.10;}
 else{hue=31;sat=.12;}
 if(s<.12){hue=36;sat=.11;}
 let target=luma(rgb);if(target<.27)target*=.94;
 let low=0,high=1;for(let i=0;i<16;i++){let mid=(low+high)/2;if(luma(fromHsl(hue,sat,mid))<target)low=mid;else high=mid}
 return fromHsl(hue,sat,(low+high)/2).map(Math.round);
}
const colorRE=/\/\*[\s\S]*?\*\/|url\((?:[^()"']|"(?:\\.|[^"])*"|'(?:\\.|[^'])*')*\)|"(?:\\.|[^"])*"|'(?:\\.|[^'])*'|#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{4}\b|#[0-9a-fA-F]{3}\b|rgba?\(\s*[\d.]+%?\s*(?:,\s*|\s+)[\d.]+%?\s*(?:,\s*|\s+)[\d.]+%?(?:\s*(?:,|\/)\s*[\d.]+%?)?\s*\)/gi;
function recolor(s){return s.replace(colorRE,(m,offset)=>{
 if(m[0]==="#"){
   // Hex selectors are not color declarations.
   const left=s.slice(Math.max(0,offset-80),offset);const right=s.slice(offset+m.length,offset+m.length+15);
   if(/^\s*(?:[>{,+~.]|\[|:not\()/.test(right)&&!/:([^{};]*)$/.test(left))return m;
   let h=m.slice(1);if(h.length<=4)h=h.split("").map(v=>v+v).join("");
   const rgb=h.slice(0,6).match(/../g).map(v=>parseInt(v,16));const n=rgbHex(mapRGB(rgb));
   if(n===h.slice(0,6).toLowerCase())return m;
   return "#"+n+h.slice(6);
 }
 if(!/^rgba?\(/i.test(m))return m;
 const body=m.slice(m.indexOf("(")+1,-1),parts=[...body.matchAll(/[\d.]+%?/g)];
 if(parts.length<3)return m;
 const v=parts.slice(0,3).map(p=>p[0].endsWith("%")?parseFloat(p[0])*2.55:parseFloat(p[0]));
 const mapped=mapRGB(v);let j=0;
 return m.replace(/[\d.]+%?/g,x=>j<3?String(Math.round(mapped[j++])):x);
});}

module.exports={recolor,mapRGB,rgbHex};
