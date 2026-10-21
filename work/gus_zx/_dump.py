import json,os
base=r"D:\DSH\军事游戏汉化\work\gus_zx"
names=[l.strip() for l in open(os.path.join(base,"batch-3.txt"),encoding="utf-8") if l.strip()]
out=[]
for n in names:
    p=os.path.join(base,"src",n)
    with open(p,encoding="utf-8",newline="") as f:
        data=f.read()
    trailing = data.endswith("\r\n") or data.endswith("\n")
    lines=data.split("\n")
    if len(lines)>1 and lines[-1]=="":
        lines=lines[:-1]
    elif len(lines)==1 and lines[0]=="":
        lines=[]
    lines=[l[:-1] if l.endswith("\r") else l for l in lines]
    out.append({"name":n,"crlf":data.count("\r\n"),"nlines":len(lines),"trailing":trailing,"lines":lines})
with open(os.path.join(base,"work_read.json"),"w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=1)
with open(os.path.join(base,"_dump.txt"),"w",encoding="utf-8") as f:
    for e in out:
        f.write("=== %s | lines=%d crlf=%d trailing=%s\n" % (e["name"],e["nlines"],e["crlf"],e["trailing"]))
        for i,l in enumerate(e["lines"],1):
            f.write("%d|%s\n"%(i,l))
