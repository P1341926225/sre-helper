import subprocess
import os
import yaml
from datetime import datetime

def load_config(config_path="config.yaml"):
	with open(config_path,'r',encoding='utf-8') as f:
		config=yaml.safe_load(f)
	return config["checks"]
	
def run_cmd(command):
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def check_cpu(threshold=80):
    output = run_cmd("top -bn1 | grep 'Cpu(s)'")
    before_id = output.split(' id,')[0]
    parts = before_id.split()
    idle = float(parts[-1])
    usage = 100 - idle
    if usage < threshold:
        status = "OK"
    else:
        status = "WARN"
    return {
        "item": "CPU使用率",
        "value": f"{usage:.1f}%",
        "threshold": f"{threshold}%",
        "status": status
    }

def check_memory(threshold=80):
	output=run_cmd("free -m | grep 'Mem'")
	output1=output.split()
	total=int(output1[1])
	available=int(output1[6])
	usage=float((total-available)/total*100)
	if usage<80:
		status="OK"
	else:
		status="WARN"
	return {
	 	'item':'内存使用率',
		'value':f'{usage:.1f}%',
		'threshold':f'{threshold}%',
		'status':status
	}

def check_disk(threshold=80):
	output=run_cmd("df -h / | tail -1")
	output1=output.split()[-2]
	usage=int(output1.strip("%"))
	if usage<80:
		status='OK'
	else:
		status='WARN'
	return {
		'item':'磁盘使用率',
		'value':f'{usage}%',
		'threshold':f'{threshold}%',
		'status':status
}

def run_inspection():
	results=[]
	checks=load_config()
	for check in checks:
		check_type=check["type"]
		if check_type=="cpu":
			threshold=check["threshold"]
			result=check_cpu(threshold)
		elif check_type=="memory":
			threshold=check["threshold"]
			result=check_memory(threshold)
		elif check_type=="disk":
			threshold=check["threshold"]
			result=check_disk(threshold)
		elif check_type=="process":
			process_name=check["target"]
			result=check_process(process_name)
		elif check_type=="port":
			port=check["target"]
			result=check_port(port)
		else:
			continue
		results.append(result)
	return results

def print_report(results,save_to_file=True):
	lines=[]
	lines.append("="*50)
	now=datetime.now()
	time_str=now.strftime('%Y-%m-%d %H:%M:%S')
	lines.append(f" 服务器巡检报告  - {time_str}")
	lines.append("="*50)

	for r in results:
		status=r["status"]
		if status=="OK":
			symbol="[OK]"
		elif status=="WARN":
			symbol="[WARN]"
		else:
			symbol="[FAIL]"
		if "threshold" in r:
			lines.append(f"{symbol} {r['item']}:{r['value']}(阈值:{r['threshold']})")
		else:
			lines.append(f"{symbol} {r['item']}:{r['value']}")
	lines.append("="*50)
	report_text="\n".join(lines)
	print(report_text)
	if save_to_file:
		os.makedirs("reports",exist_ok=True)
		filename=now.strftime("inspection_%Y%m%d_%H%M%S.log")
		filepath=os.path.join("reports",filename)
		with open(filepath,"w",encoding="utf-8") as f:
			f.write(report_text)
		print(f"报告已保存:{filepath}")

def check_process(process_name):
	output=int(run_cmd(f"ps aux | grep {process_name} | grep -v grep | wc -l"))
	if output>0:
		status="OK"
	else:
		status="FAIL"
	return {
		"item":f"进程[{process_name}]",
		"value":"运行中" if output>0 else "未运行",
		"status":status
}

def check_port(port):
	output=int(run_cmd(f"ss -tlnp | grep ':{port}' | wc -l"))
	if output>0:
		status="OK"
	else:
		status="FAIL"
	return {
		"item":f"端口[{port}]",
		"value":"监听中" if output>0 else "未监听",
		"status":status
}

if __name__=="__main__":
	results=run_inspection()
	print_report(results)

