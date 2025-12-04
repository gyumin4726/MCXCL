#!/usr/bin/env python3
"""
유리(Glass) 매질 데이터 생성 스크립트
RNG 시드만 변경하여 다양한 노이즈 패턴 생성
"""

import json
import os
import subprocess
import base64
import zlib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_directories():
    """필요한 디렉토리 생성"""
    dirs = ['data', 'data/jnii', 'data/jdat', 'data/json', 'images']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
    print("✅ 디렉토리 구조 생성 완료")

def create_glass_configs(num_samples=5):
    """지정된 개수의 유리 시뮬레이션 설정 파일 생성"""
    
    # 기본 설정 (glass_simulation.json 기준)
    base_config = {
        "Domain": {
            "VolumeFile": "cubic60.json",
            "Dim": [60, 60, 60],
            "OriginType": 1,
            "LengthUnit": 1.0,
            "Media": [
                {"mua": 0.00, "mus": 0.0, "g": 1.00, "n": 1.0},
                {"mua": 0.0001, "mus": 0.0, "g": None, "n": 1.52}  # 유리의 광학적 특성
            ]
        },
        "Session": {
            "Photons": 1000,
            "RNGSeed": 12345,  # 이 값만 변경
            "ID": "glass_test1"  # 이 값도 변경
        },
        "Forward": {
            "T0": 0.0e-09,
            "T1": 5.0e-09,
            "Dt": 1.0e-09
        },
        "Optode": {
            "Source": {
                "Pos": [30.0, 30.0, 0.0],
                "Dir": [0.0, 0.0, 1.0],
                "Type": "isotropic"
            },
            "Detector": [
                {"Pos": [30.0, 20.0, 0.0], "R": 2.0},
                {"Pos": [30.0, 40.0, 0.0], "R": 2.0},
                {"Pos": [20.0, 30.0, 0.0], "R": 2.0},
                {"Pos": [40.0, 30.0, 0.0], "R": 2.0}
            ]
        }
    }
    
    # 지정된 개수의 설정 파일 생성
    configs = []
    for i in range(1, num_samples + 1):
        config = base_config.copy()
        config["Session"]["RNGSeed"] = 12345 + i  # 12346, 12347, 12348, 12349, 12350
        config["Session"]["ID"] = f"glass{i:03d}"
        
        # 설정 파일 저장 (data/json 폴더에)
        config_file = f"data/json/glass_simulation_{i}.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        configs.append(config_file)
        print(f"✅ 설정 파일 생성: {config_file} (RNGSeed: {12345 + i})")
    
    print(f"📝 총 {num_samples}개의 설정 파일 생성 완료")
    
    return configs

def run_simulations(configs):
    """시뮬레이션 실행"""
    total_samples = len(configs)
    print(f"\n🚀 시뮬레이션 실행 시작... (총 {total_samples}개)")
    
    success_count = 0
    for i, config_file in enumerate(configs, 1):
        print(f"\n--- 시뮬레이션 {i}/{total_samples} 실행 중 ---")
        
        try:
            # MCXCL 실행
            cmd = f"/mnt/c/Users/user/Downloads/MCXCL/bin/mcxcl -f {config_file} -g 0"
            print(f"명령어: {cmd}")
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ 성공: {config_file}")
                success_count += 1
                
                # 결과 파일들을 적절한 폴더로 이동
                move_result_files(i)
            else:
                print(f"❌ 실패: {config_file}")
                print(f"오류: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 예외 발생: {config_file} - {e}")
    
    return success_count

def move_result_files(sample_id):
    """결과 파일들을 적절한 폴더로 이동"""
    try:
        # jnii 파일 이동 (새로운 파일명 형식)
        jnii_file = f"glass{sample_id:03d}.jnii"
        if os.path.exists(jnii_file):
            os.rename(jnii_file, f"data/jnii/{jnii_file}")
            print(f"  📁 이동됨: {jnii_file} -> data/jnii/")
        else:
            # _vol이 있는 경우도 확인
            jnii_file_vol = f"glass{sample_id:03d}_vol.jnii"
            if os.path.exists(jnii_file_vol):
                os.rename(jnii_file_vol, f"data/jnii/{jnii_file}")
                print(f"  📁 이동됨: {jnii_file_vol} -> data/jnii/{jnii_file}")
        
        # jdat 파일 이동
        jdat_file = f"glass{sample_id:03d}_detp.jdat"
        if os.path.exists(jdat_file):
            os.rename(jdat_file, f"data/jdat/{jdat_file}")
            print(f"  📁 이동됨: {jdat_file} -> data/jdat/")
            
    except Exception as e:
        print(f"  ⚠️ 파일 이동 중 오류: {e}")

def extract_jnifti_data(jnii_file):
    """JNIfTI 파일에서 이미지 데이터를 추출"""
    print(f"📖 JNIfTI 파일 읽는 중: {jnii_file}")
    
    with open(jnii_file, 'r') as f:
        data = json.load(f)
    
    # 이미지 데이터 추출
    nifti_data = data['NIFTIData']
    array_data = nifti_data['_ArrayZipData_']
    
    # Base64 디코딩
    decoded = base64.b64decode(array_data)
    
    # Zlib 압축 해제
    decompressed = zlib.decompress(decoded)
    
    # NumPy 배열로 변환
    array = np.frombuffer(decompressed, dtype=np.float32)
    
    # 차원 정보 가져오기
    array_size = nifti_data['_ArraySize_']
    print(f"  📊 배열 크기: {array_size}")
    
    # 4D 배열로 재구성 (x, y, z, time)
    array = array.reshape(array_size)
    
    return array, data

def visualize_glass_samples():
    """유리 샘플들을 시각화"""
    print("\n🎨 이미지 생성 시작...")
    
    # 모든 jnii 파일 찾기
    jnii_files = [f for f in os.listdir('data/jnii') if f.endswith('.jnii')]
    jnii_files.sort()
    
    if not jnii_files:
        print("❌ jnii 파일을 찾을 수 없습니다.")
        return
    
    print(f"📁 발견된 jnii 파일: {len(jnii_files)}개")
    
    # 각 샘플별로 이미지 생성
    for i, jnii_file in enumerate(jnii_files, 1):
        print(f"\n--- 샘플 {i}/{len(jnii_files)} 시각화 중 ---")
        
        try:
            # 데이터 추출
            array, metadata = extract_jnifti_data(f'data/jnii/{jnii_file}')
            
            # Gate 2 데이터 추출 (산란이 있는 광자들)
            gate2_data = array[:, :, :, 1]  # Gate 2 (1-2ns)
            
            # 중간 z-슬라이스 시각화
            z_slice = gate2_data.shape[2] // 2
            fluence_map = gate2_data[:, :, z_slice]
            
            # 순수 이미지 생성 (224x224 픽셀)
            plt.figure(figsize=(2.24, 2.24))  # 2.24x2.24 인치
            plt.imshow(fluence_map.T, cmap='hot', origin='lower')
            plt.axis('off')  # 모든 축과 라벨 제거
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)  # 여백 제거
            
            # 이미지 저장 (224x224 픽셀)
            output_file = f'images/glass{i:03d}.png'
            plt.savefig(output_file, dpi=100, bbox_inches='tight', pad_inches=0)
            plt.close()
            
            print(f"  ✅ 이미지 저장: {output_file}")
            
        except Exception as e:
            print(f"  ❌ 시각화 실패: {jnii_file} - {e}")
    
    # 개별 이미지만 생성 (비교 이미지 제거)


def main():
    """메인 함수"""
    print("🪟 유리(Glass) 매질 데이터 생성 및 시각화")
    print("=" * 50)
    
    # 사용자 입력으로 샘플 개수 받기
    try:
        num_samples = int(input("생성할 샘플 개수를 입력하세요 (기본값: 5): ") or "5")
    except ValueError:
        num_samples = 5
        print("잘못된 입력입니다. 기본값 5개로 설정합니다.")
    
    # 현재 디렉토리 확인
    if not os.path.exists("glass_simulation.json"):
        print("❌ 오류: glass_simulation.json 파일을 찾을 수 없습니다.")
        print("glass 디렉토리에서 실행해주세요.")
        return
    
    # 1. 디렉토리 구조 생성
    print("\n📁 디렉토리 구조 생성 중...")
    create_directories()
    
    # 2. cubic60.json 파일 복사
    if not os.path.exists("cubic60.json"):
        if os.path.exists("../cubic60.json"):
            subprocess.run("cp ../cubic60.json .", shell=True)
            print("✅ cubic60.json 파일 복사 완료")
        else:
            print("❌ 오류: cubic60.json 파일을 찾을 수 없습니다.")
            return
    
    # 3. 설정 파일 생성
    print(f"\n📝 설정 파일 생성 중... ({num_samples}개)")
    configs = create_glass_configs(num_samples)
    
    # 4. 시뮬레이션 실행
    success_count = run_simulations(configs)
    
    # 5. 이미지 생성
    if success_count > 0:
        visualize_glass_samples()
    
    # 6. 결과 요약
    print(f"\n📊 생성 완료!")
    print(f"✅ 성공: {success_count}/{num_samples}")
    print(f"❌ 실패: {num_samples - success_count}")
    
    if success_count > 0:
        print(f"\n📁 생성된 파일 구조:")
        print(f"  data/json/     - 설정 파일들")
        print(f"  data/jnii/     - 시뮬레이션 결과 (3D 데이터)")
        print(f"  data/jdat/     - 탐지기 데이터")
        print(f"  images/        - 시각화된 이미지들")
        
        print(f"\n🖼️ 생성된 이미지들:")
        for i in range(1, success_count + 1):
            print(f"  - glass{i:03d}.png")
    
    print(f"\n🎉 모든 작업 완료!")

if __name__ == "__main__":
    main()