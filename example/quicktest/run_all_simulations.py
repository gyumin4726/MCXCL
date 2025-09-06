#!/usr/bin/env python3
"""
MCX-CL을 사용한 다중 매질 시뮬레이션 실행 스크립트
"""

import subprocess
import os
import json

def run_simulation(config_file, output_prefix, photons=100000):
    """시뮬레이션 실행"""
    print(f"\n=== {output_prefix.upper()} 시뮬레이션 실행 ===")
    
    # MCX-CL 실행
    cmd = [
        "../../bin/mcxcl",
        "-f", config_file,
        "-n", str(photons),
        "-s", output_prefix
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {output_prefix} 시뮬레이션 완료")
        print(f"출력: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {output_prefix} 시뮬레이션 실패")
        print(f"오류: {e.stderr}")
        return False

def main():
    """메인 함수"""
    print("MCX-CL 다중 매질 시뮬레이션 시작")
    
    # 시뮬레이션 설정
    simulations = [
        {
            "config": "air/air_simulation.json",
            "output": "air/air_result",
            "description": "Air (n=1.0)"
        },
        {
            "config": "water/water_simulation.json", 
            "output": "water/water_result",
            "description": "Water (n=1.33)"
        },
        {
            "config": "glass/glass_simulation.json",
            "output": "glass/glass_result", 
            "description": "Glass (n=1.5)"
        }
    ]
    
    # 각 시뮬레이션 실행
    results = []
    for sim in simulations:
        if os.path.exists(sim["config"]):
            success = run_simulation(sim["config"], sim["output"])
            results.append({
                "name": sim["description"],
                "success": success,
                "output": sim["output"]
            })
        else:
            print(f"❌ 설정 파일을 찾을 수 없음: {sim['config']}")
            results.append({
                "name": sim["description"],
                "success": False,
                "output": sim["output"]
            })
    
    # 결과 요약
    print("\n" + "="*50)
    print("시뮬레이션 결과 요약")
    print("="*50)
    
    for result in results:
        status = "✅ 성공" if result["success"] else "❌ 실패"
        print(f"{result['name']}: {status}")
 
if __name__ == "__main__":
    main()
