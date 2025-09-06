#!/usr/bin/env python3
"""
유리 매질 시뮬레이션 시각화 스크립트
"""

import json
import base64
import zlib
import numpy as np
import matplotlib.pyplot as plt
import os

def extract_jnifti_data(jnii_file):
    """JNIfTI 파일에서 이미지 데이터를 추출"""
    print(f"JNIfTI 파일 읽는 중: {jnii_file}")
    
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
    print(f"배열 크기: {array_size}")
    
    # 4D 배열로 재구성 (x, y, z, time)
    array = array.reshape(array_size)
    
    return array, data

def visualize_fluence_map(array, output_dir='.', material_name='Glass'):
    """Fluence Map을 시각화"""
    print("Fluence Map 시각화 중...")
    
    # Gate 1의 최대값과 최소값 계산
    gate1_min = np.min(array[:, :, :, 0])
    gate1_max = np.max(array[:, :, :, 0])
    print(f"Gate 1 범위: {gate1_min:.6f} ~ {gate1_max:.6f}")
    
    # Gate 2-5의 최대값과 최소값 계산
    gate2_5_data = array[:, :, :, 1:5]  # Gate 2-5만
    gate2_5_min = np.min(gate2_5_data)
    gate2_5_max = np.max(gate2_5_data)
    print(f"Gate 2-5 범위: {gate2_5_min:.6f} ~ {gate2_5_max:.6f}")
    
    # 시간 게이트별로 슬라이스 시각화
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'{material_name} Medium - Fluence Map (Time Gates) - Gate 2-5 Same Scale', fontsize=16)
    
    for i in range(min(5, array.shape[3])):
        row = i // 3
        col = i % 3
        
        # 중간 z-슬라이스 시각화
        z_slice = array.shape[2] // 2
        
        if i == 0:  # Gate 1은 자체 스케일
            im = axes[row, col].imshow(array[:, :, z_slice, i], cmap='hot', origin='lower')
            axes[row, col].set_title(f'Time Gate {i+1} (z={z_slice}) - Auto Scale')
        else:  # Gate 2-5는 동일한 스케일
            im = axes[row, col].imshow(array[:, :, z_slice, i], cmap='hot', origin='lower', 
                                     vmin=gate2_5_min, vmax=gate2_5_max)
            axes[row, col].set_title(f'Time Gate {i+1} (z={z_slice}) - Gate 2-5 Scale')
        
        axes[row, col].set_xlabel('X')
        axes[row, col].set_ylabel('Y')
        plt.colorbar(im, ax=axes[row, col])
    
    # 마지막 subplot 숨기기
    if array.shape[3] < 6:
        axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{material_name.lower()}_fluence_map.png'), dpi=300, bbox_inches='tight')
    print(f"이미지 저장됨: {material_name.lower()}_fluence_map.png")
    
    return fig

def analyze_optical_properties(array, metadata, material_name='Glass'):
    """광학 특성 분석"""
    print(f"\n=== {material_name} 광학 특성 분석 ===")
    
    # Fluence Map 통계
    print(f"Fluence Map 통계:")
    print(f"  최대값: {np.max(array):.6f}")
    print(f"  최소값: {np.min(array):.6f}")
    print(f"  평균값: {np.mean(array):.6f}")
    print(f"  표준편차: {np.std(array):.6f}")
    
    # 시간 게이트별 분석
    print(f"\n시간 게이트별 분석:")
    for t in range(array.shape[3]):
        time_slice = array[:, :, :, t]
        print(f"  게이트 {t+1}: 최대={np.max(time_slice):.6f}, 평균={np.mean(time_slice):.6f}")
    
    # 공간적 분포 분석
    print(f"\n공간적 분포 분석:")
    center_x, center_y, center_z = array.shape[0]//2, array.shape[1]//2, array.shape[2]//2
    
    # 중심에서의 분포
    center_slice = array[center_x, :, :, -1]  # 마지막 시간 게이트
    print(f"  중심 슬라이스 (z={center_z}): 최대={np.max(center_slice):.6f}")
    
    # 경계에서의 분포
    edge_slice = array[0, :, :, -1]  # 가장자리 슬라이스
    print(f"  경계 슬라이스 (x=0): 최대={np.max(edge_slice):.6f}")
    
    # 시뮬레이션 설정 파일에서 정보 가져오기
    try:
        config_file = f'{material_name.lower()}_simulation.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"\n시뮬레이션 정보:")
            
            # 매질 정보
            if 'Domain' in config and 'Media' in config['Domain']:
                media = config['Domain']['Media']
                print(f"  매질 수: {len(media)}")
                for i, medium in enumerate(media):
                    print(f"  매질 {i}: n={medium.get('n', 'N/A')}, mua={medium.get('mua', 'N/A')}, mus={medium.get('mus', 'N/A')}")
            
            # 광자 수 정보
            if 'Session' in config and 'Photons' in config['Session']:
                total_photons = config['Session']['Photons']
                print(f"  총 광자 수: {total_photons:,}")
            
            # 검출된 광자 수 (detp 파일에서)
            detp_file = f'{material_name.lower()}_result_detp.jdat'
            if os.path.exists(detp_file):
                with open(detp_file, 'r') as f:
                    detp_data = json.load(f)
                if 'DetectedPhoton' in detp_data:
                    detected = detp_data['DetectedPhoton']
                    print(f"  검출된 광자: {detected:,}")
                    if 'Session' in config and 'Photons' in config['Session']:
                        print(f"  검출률: {detected/total_photons*100:.3f}%")
        else:
            print(f"\n시뮬레이션 정보: 설정 파일을 찾을 수 없음")
    except Exception as e:
        print(f"\n시뮬레이션 정보 분석 중 오류: {e}")
        print("기본 통계 정보만 표시합니다.")

def main():
    """메인 함수"""
    jnii_file = 'glass_result.jnii'
    
    if not os.path.exists(jnii_file):
        print(f"오류: {jnii_file} 파일을 찾을 수 없습니다.")
        print("현재 디렉토리:", os.getcwd())
        return
    
    try:
        # 이미지 데이터 추출
        array, metadata = extract_jnifti_data(jnii_file)
        
        # 시각화
        visualize_fluence_map(array, material_name='Glass')
        
        # 분석
        analyze_optical_properties(array, metadata, material_name='Glass')
        
        print("\n✅ 모든 작업이 완료되었습니다!")
        print("생성된 파일:")
        print("- glass_fluence_map.png (시간 게이트별 시각화)")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
