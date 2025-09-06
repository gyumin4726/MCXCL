# MCX-CL 환경 설정 및 사용 가이드

## 개요

MCX-CL (Monte Carlo eXtreme - OpenCL Edition)은 다양한 하드웨어(CPU, GPU)에서 실행 가능한 광자 전송 시뮬레이션 소프트웨어입니다. 이 가이드는 Windows 환경에서 WSL을 사용하여 MCX-CL을 설정하고 사용하는 방법을 설명합니다.

- **Author:** Qianqian Fang (q.fang at neu.edu)
- **License:** GNU General Public License version 3 (GPLv3)
- **Version:** 1.6 (Harmonic)
- **Website:** [https://mcx.space](https://mcx.space)

## 목차

- [시스템 요구사항](#시스템-요구사항)
- [1단계: WSL 환경 설정](#1단계-wsl-환경-설정)
- [2단계: MCX-CL 소스코드 다운로드 및 빌드](#2단계-mcx-cl-소스코드-다운로드-및-빌드)
- [3단계: 테스트 시뮬레이션 실행](#3단계-테스트-시뮬레이션-실행)
- [4단계: 연구용 데이터 생성 스크립트 작성](#4단계-연구용-데이터-생성-스크립트-작성)
- [5단계: 시뮬레이션 실행 및 시각화](#5단계-시뮬레이션-실행-및-시각화)
- [6단계: 결과 확인](#6단계-결과-확인)
- [7단계: PINN 모델을 위한 데이터 준비](#7단계-pinn-모델을-위한-데이터-준비)
- [문제 해결](#문제-해결)
- [추가 정보](#추가-정보)

## 시스템 요구사항

- Windows 10/11 with WSL (Windows Subsystem for Linux)
- Ubuntu 20.04+ (WSL 내부)
- OpenCL 지원 CPU 또는 GPU
- 최소 4GB RAM (8GB 권장)

## 1단계: WSL 환경 설정

### 1.1 WSL 설치 및 Ubuntu 설정

```bash
# Windows PowerShell (관리자 권한)에서 실행
wsl --install -d Ubuntu-20.04
```

### 1.2 Ubuntu 업데이트 및 필수 패키지 설치

```bash
# WSL Ubuntu 터미널에서 실행
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential cmake git wget curl
sudo apt install -y ocl-icd-libopencl1 opencl-headers ocl-icd-opencl-dev
sudo apt install -y zlib1g-dev liboctave-dev
sudo apt install -y python3-dev python3-pip python3-wheel
```

## 2단계: MCX-CL 소스코드 다운로드 및 빌드

### 2.1 저장소 클론

```bash
cd ~
git clone https://github.com/fangq/mcxcl.git
cd mcxcl
```

### 2.2 빌드 환경 설정

```bash
# src 디렉토리로 이동
cd src

# 빌드 디렉토리 생성
mkdir build
cd build

# CMake 설정
cmake ../src

# 컴파일
make -j$(nproc)
```

### 2.3 빌드 확인

```bash
# 실행 파일 위치 확인
ls -la ../bin/mcxcl

# OpenCL 지원 하드웨어 확인
../bin/mcxcl -L
```

## 3단계: 테스트 시뮬레이션 실행

### 3.1 예제 파일 복사

```bash
# 프로젝트 루트로 이동
cd /mnt/d/mcxcl

# 예제 파일 복사
cp example/quicktest/cubic60.json .
cp example/quicktest/qtest.json .
```

### 3.2 기본 테스트 실행

```bash
# 간단한 테스트 실행
./bin/mcxcl -f qtest.json -n 10000
```

## 4단계: 연구용 데이터 생성 스크립트 작성

### 4.1 매질별 시뮬레이션 설정 파일 생성

#### Air (공기) 시뮬레이션
```bash
mkdir -p air
cat > air/air_simulation.json << 'EOF'
{
    "Domain": {
        "VolumeFile": "cubic60.json",
        "Dim": [60, 60, 60],
        "OriginType": 1,
        "LengthUnit": 1.0,
        "Media": [
            {"mua": 0.00, "mus": 0.0, "g": 1.00, "n": 1.0},
            {"mua": 0.00, "mus": 0.0, "g": 1.00, "n": 1.0}
        ]
    },
    "Session": {"Photons": 100000, "RNGSeed": 12345, "ID": "air_test"},
    "Forward": {"T0": 0.0e+00, "T1": 5.0e-09, "Dt": 1.0e-09},
    "Optode": {
        "Source": {"Pos": [30.0, 30.0, 0.0], "Dir": [0.0, 0.0, 1.0], "Type": "pencil"},
        "Detector": [
            {"Pos": [30.0, 20.0, 0.0], "R": 2.0},
            {"Pos": [30.0, 40.0, 0.0], "R": 2.0},
            {"Pos": [20.0, 30.0, 0.0], "R": 2.0},
            {"Pos": [40.0, 30.0, 0.0], "R": 2.0}
        ]
    }
}
EOF
```

#### Water (물) 시뮬레이션
```bash
mkdir -p water
cat > water/water_simulation.json << 'EOF'
{
    "Domain": {
        "VolumeFile": "cubic60.json",
        "Dim": [60, 60, 60],
        "OriginType": 1,
        "LengthUnit": 1.0,
        "Media": [
            {"mua": 0.00, "mus": 0.0, "g": 1.00, "n": 1.0},
            {"mua": 0.001, "mus": 0.1, "g": 0.9, "n": 1.33}
        ]
    },
    "Session": {"Photons": 100000, "RNGSeed": 12345, "ID": "water_test"},
    "Forward": {"T0": 0.0e+00, "T1": 5.0e-09, "Dt": 1.0e-09},
    "Optode": {
        "Source": {"Pos": [30.0, 30.0, 0.0], "Dir": [0.0, 0.0, 1.0], "Type": "pencil"},
        "Detector": [
            {"Pos": [30.0, 20.0, 0.0], "R": 2.0},
            {"Pos": [30.0, 40.0, 0.0], "R": 2.0},
            {"Pos": [20.0, 30.0, 0.0], "R": 2.0},
            {"Pos": [40.0, 30.0, 0.0], "R": 2.0}
        ]
    }
}
EOF
```

#### Glass (유리) 시뮬레이션
```bash
mkdir -p glass
cat > glass/glass_simulation.json << 'EOF'
{
    "Domain": {
        "VolumeFile": "cubic60.json",
        "Dim": [60, 60, 60],
        "OriginType": 1,
        "LengthUnit": 1.0,
        "Media": [
            {"mua": 0.00, "mus": 0.0, "g": 1.00, "n": 1.0},
            {"mua": 0.01, "mus": 1.0, "g": 0.8, "n": 1.5}
        ]
    },
    "Session": {"Photons": 100000, "RNGSeed": 12345, "ID": "glass_test"},
    "Forward": {"T0": 0.0e+00, "T1": 5.0e-09, "Dt": 1.0e-09},
    "Optode": {
        "Source": {"Pos": [30.0, 30.0, 0.0], "Dir": [0.0, 0.0, 1.0], "Type": "pencil"},
        "Detector": [
            {"Pos": [30.0, 20.0, 0.0], "R": 2.0},
            {"Pos": [30.0, 40.0, 0.0], "R": 2.0},
            {"Pos": [20.0, 30.0, 0.0], "R": 2.0},
            {"Pos": [40.0, 30.0, 0.0], "R": 2.0}
        ]
    }
}
EOF
```

### 4.2 자동화 스크립트 생성

```bash
cat > run_all_simulations.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import os
import sys

def run_simulation(config_file, output_prefix, description):
    """MCX-CL 시뮬레이션 실행"""
    print(f"\n=== {description} 시뮬레이션 시작 ===")
    
    try:
        # MCX-CL 명령어 실행
        cmd = [
            './bin/mcxcl',
            '-f', config_file,
            '-s', output_prefix,
            '-n', '100000',
            '-F', 'jnii'  # JNIfTI 형식으로 출력
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} 시뮬레이션 완료")
        print(f"출력 파일: {output_prefix}_flux.jnii")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 시뮬레이션 실패")
        print(f"오류: {e.stderr}")
        return False

def main():
    """모든 시뮬레이션 실행"""
    print("MCX-CL 연구용 데이터 생성 시작")
    
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
    success_count = 0
    for sim in simulations:
        if run_simulation(sim["config"], sim["output"], sim["description"]):
            success_count += 1
    
    print(f"\n=== 시뮬레이션 완료 ===")
    print(f"성공: {success_count}/{len(simulations)}")
    
    if success_count == len(simulations):
        print("✅ 모든 시뮬레이션이 성공적으로 완료되었습니다!")
    else:
        print("⚠️ 일부 시뮬레이션이 실패했습니다.")

if __name__ == "__main__":
    main()
EOF

chmod +x run_all_simulations.py
```

### 4.3 시각화 스크립트 생성

```bash
cat > visualize_all.py << 'EOF'
#!/usr/bin/env python3
import json
import base64
import zlib
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

def load_jnii_data(file_path):
    """JNIfTI 파일에서 데이터 로드"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    nifti_data = data['NIFTIData']
    array_data = nifti_data['_ArrayZipData_']
    decoded = base64.b64decode(array_data)
    decompressed = zlib.decompress(decoded)
    array = np.frombuffer(decompressed, dtype=np.float32)
    array_size = nifti_data['_ArraySize_']
    array = array.reshape(array_size)
    
    return array

def normalize_all_gates(arrays, materials):
    """모든 매질의 동일한 게이트에 대해 정규화 범위 계산"""
    gate_ranges = []
    
    for gate_idx in range(5):  # 5개 타임 게이트
        gate_min = float('inf')
        gate_max = float('-inf')
        
        for array in arrays:
            gate_data = array[:, :, :, gate_idx]
            gate_min = min(gate_min, np.min(gate_data[gate_data > 0]))
            gate_max = max(gate_max, np.max(gate_data))
        
        gate_ranges.append((gate_min, gate_max))
    
    return gate_ranges

def visualize_fluence_map(array, output_dir, material_name, gate_ranges=None):
    """Fluence Map 시각화"""
    z_slice = 30  # 중간 슬라이스
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'{material_name} Fluence Map (z={z_slice})', fontsize=16)
    
    for i in range(5):
        row = i // 3
        col = i % 3
        
        if gate_ranges is not None:
            gate_min, gate_max = gate_ranges[i]
            im = axes[row, col].imshow(array[:, :, z_slice, i], cmap='hot', origin='lower',
                                     vmin=gate_min, vmax=gate_max)
            axes[row, col].set_title(f'Time Gate {i+1} (z={z_slice}) - Normalized')
        else:
            im = axes[row, col].imshow(array[:, :, z_slice, i], cmap='hot', origin='lower')
            axes[row, col].set_title(f'Time Gate {i+1} (z={z_slice}) - Auto Scale')
        
        axes[row, col].set_xlabel('X')
        axes[row, col].set_ylabel('Y')
        plt.colorbar(im, ax=axes[row, col])
    
    # 마지막 subplot 숨기기
    axes[1, 2].set_visible(False)
    
    plt.tight_layout()
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'{material_name.lower()}_fluence_map.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file

def create_comparison_visualization(arrays, materials, output_dir):
    """매질 비교 시각화"""
    z_slice = 30
    
    fig, axes = plt.subplots(3, 5, figsize=(20, 12))
    fig.suptitle('Material Comparison - Fluence Maps (z=30)', fontsize=16)
    
    for material_idx, (material, array) in enumerate(zip(materials, arrays)):
        for gate_idx in range(5):
            im = axes[material_idx, gate_idx].imshow(
                array[:, :, z_slice, gate_idx], 
                cmap='hot', origin='lower'
            )
            axes[material_idx, gate_idx].set_title(f'{material} - Gate {gate_idx+1}')
            axes[material_idx, gate_idx].set_xlabel('X')
            axes[material_idx, gate_idx].set_ylabel('Y')
            plt.colorbar(im, ax=axes[material_idx, gate_idx])
    
    plt.tight_layout()
    
    output_file = os.path.join(output_dir, 'material_comparison.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_file

def analyze_optical_properties(array, material_name):
    """광학적 특성 분석"""
    print(f"\n=== {material_name} 광학적 특성 분석 ===")
    
    for i in range(5):
        gate_data = array[:, :, :, i]
        non_zero_data = gate_data[gate_data > 0]
        
        if len(non_zero_data) > 0:
            print(f"Gate {i+1}: 최대값={np.max(gate_data):.6f}, 평균값={np.mean(non_zero_data):.6f}")
        else:
            print(f"Gate {i+1}: 데이터 없음")

def main():
    """메인 함수"""
    print("MCX-CL Fluence Map 시각화 시작")
    
    # 매질별 데이터 로드
    materials = ['Air', 'Water', 'Glass']
    material_dirs = ['air', 'water', 'glass']
    arrays = []
    
    for material, material_dir in zip(materials, material_dirs):
        jnii_file = f'{material_dir}/{material_dir}_result_flux.jnii'
        if os.path.exists(jnii_file):
            print(f"로딩 중: {jnii_file}")
            array = load_jnii_data(jnii_file)
            arrays.append(array)
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {jnii_file}")
            return
    
    # 모든 타임 게이트 정규화 범위 계산
    if len(arrays) >= 2:
        print("정규화 범위 계산 중...")
        gate_ranges = normalize_all_gates(arrays, materials)
    else:
        gate_ranges = None
    
    # 출력 디렉토리 생성
    output_dir = 'visualize'
    os.makedirs(output_dir, exist_ok=True)
    
    # 개별 매질 시각화 (정규화된 스케일 사용)
    for i, (material, material_dir, array) in enumerate(zip(materials, material_dirs, arrays)):
        print(f"시각화 중: {material}")
        output_file = visualize_fluence_map(array, output_dir, material, gate_ranges)
        print(f"저장됨: {output_file}")
        
        # 광학적 특성 분석
        analyze_optical_properties(array, material)
    
    # 매질 비교 시각화
    print("매질 비교 시각화 중...")
    comparison_file = create_comparison_visualization(arrays, materials, output_dir)
    print(f"저장됨: {comparison_file}")
    
    print(f"\n✅ 모든 시각화가 완료되었습니다!")
    print(f"출력 디렉토리: {output_dir}/")

if __name__ == "__main__":
    main()
EOF

chmod +x visualize_all.py
```

## 5단계: 시뮬레이션 실행 및 시각화

### 5.1 모든 시뮬레이션 실행

```bash
python3 run_all_simulations.py
```

### 5.2 결과 시각화

```bash
python3 visualize_all.py
```

## 6단계: 결과 확인

### 6.1 생성된 파일들

```bash
# 시뮬레이션 결과 파일들
ls -la air/water/glass/*.jnii

# 시각화 결과 파일들
ls -la visualize/*.png
```

### 6.2 주요 출력 파일

- **시뮬레이션 결과**: `{material}_result_flux.jnii` (JNIfTI 형식)
- **시각화 결과**: 
  - `{material}_fluence_map.png` (개별 매질)
  - `material_comparison.png` (매질 비교)

## 7단계: PINN 모델을 위한 데이터 준비

### 7.1 데이터 전처리 스크립트

```bash
cat > prepare_pinn_data.py << 'EOF'
#!/usr/bin/env python3
import json
import base64
import zlib
import numpy as np
import os

def load_jnii_data(file_path):
    """JNIfTI 파일에서 데이터 로드"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    nifti_data = data['NIFTIData']
    array_data = nifti_data['_ArrayZipData_']
    decoded = base64.b64decode(array_data)
    decompressed = zlib.decompress(decoded)
    array = np.frombuffer(decompressed, dtype=np.float32)
    array_size = nifti_data['_ArraySize_']
    array = array.reshape(array_size)
    
    return array

def prepare_training_data():
    """PINN 모델을 위한 훈련 데이터 준비"""
    materials = ['air', 'water', 'glass']
    pinn_data = {}
    
    for material in materials:
        jnii_file = f'{material}/{material}_result_flux.jnii'
        if os.path.exists(jnii_file):
            print(f"로딩 중: {jnii_file}")
            array = load_jnii_data(jnii_file)
            
            # Time Gate 2 데이터 추출 (PINN 입력으로 적합)
            gate2_data = array[:, :, :, 1]  # 0-indexed
            
            pinn_data[material] = {
                'fluence_map': gate2_data,
                'optical_properties': get_optical_properties(material)
            }
    
    return pinn_data

def get_optical_properties(material):
    """매질별 광학적 특성 반환"""
    properties = {
        'air': {'n': 1.0, 'mua': 0.0, 'mus': 0.0, 'g': 1.0},
        'water': {'n': 1.33, 'mua': 0.001, 'mus': 0.1, 'g': 0.9},
        'glass': {'n': 1.5, 'mua': 0.01, 'mus': 1.0, 'g': 0.8}
    }
    return properties.get(material, {})

def save_pinn_data(pinn_data, output_dir='pinn_data'):
    """PINN 데이터 저장"""
    os.makedirs(output_dir, exist_ok=True)
    
    for material, data in pinn_data.items():
        # NumPy 배열로 저장
        np.save(f'{output_dir}/{material}_fluence_map.npy', data['fluence_map'])
        
        # 광학적 특성 저장
        with open(f'{output_dir}/{material}_properties.json', 'w') as f:
            json.dump(data['optical_properties'], f, indent=2)
    
    print(f"✅ PINN 데이터가 {output_dir}/ 디렉토리에 저장되었습니다!")

if __name__ == "__main__":
    print("PINN 모델을 위한 데이터 준비 시작")
    
    pinn_data = prepare_training_data()
    save_pinn_data(pinn_data)
    
    print("✅ 데이터 준비 완료!")
EOF

chmod +x prepare_pinn_data.py
```

### 7.2 PINN 데이터 준비

```bash
python3 prepare_pinn_data.py
```

## 문제 해결

### 일반적인 문제들

1. **OpenCL 드라이버 문제**
   ```bash
   # OpenCL 지원 확인
   ./bin/mcxcl -L
   ```

2. **메모리 부족**
   ```bash
   # 광자 수 줄이기
   ./bin/mcxcl -f config.json -n 50000
   ```

3. **권한 문제**
   ```bash
   # 실행 권한 부여
   chmod +x *.py
   chmod +x bin/mcxcl
   ```

## 추가 정보

- **MCX-CL 공식 문서**: https://mcx.space/
- **JNIfTI 형식**: https://neurojson.org/
- **OpenCL 지원**: Intel, NVIDIA, AMD GPU 및 CPU 지원

## 라이선스

GNU General Public License version 3 (GPLv3)

---

이 가이드를 따라하면 Windows 환경에서 WSL을 사용하여 MCX-CL을 설정하고, 다양한 매질에 대한 광자 전송 시뮬레이션을 실행할 수 있습니다. 생성된 Fluence Map 데이터는 PINN 모델의 입력으로 사용할 수 있습니다.
