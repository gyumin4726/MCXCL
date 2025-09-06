#!/usr/bin/env python3
"""
모든 매질 시각화를 한 번에 실행하는 스크립트
"""

import json
import base64
import zlib
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil

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

def visualize_fluence_map(array, output_dir, material_name, gate_ranges=None):
    """Fluence Map을 시각화"""
    print(f"{material_name} Fluence Map 시각화 중...")
    
    # 시간 게이트별로 슬라이스 시각화
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'{material_name} Medium - Fluence Map (Time Gates) - All Gates Normalized', fontsize=16)
    
    for i in range(min(5, array.shape[3])):
        row = i // 3
        col = i % 3
        
        # 중간 z-슬라이스 시각화
        z_slice = array.shape[2] // 2
        
        if gate_ranges is not None:
            # 정규화된 스케일 사용
            gate_min, gate_max = gate_ranges[i]
            im = axes[row, col].imshow(array[:, :, z_slice, i], cmap='hot', origin='lower',
                                     vmin=gate_min, vmax=gate_max)
            axes[row, col].set_title(f'Time Gate {i+1} (z={z_slice}) - Normalized')
        else:
            # 자체 스케일 사용
            im = axes[row, col].imshow(array[:, :, z_slice, i], cmap='hot', origin='lower')
            axes[row, col].set_title(f'Time Gate {i+1} (z={z_slice}) - Auto Scale')
        
        axes[row, col].set_xlabel('X')
        axes[row, col].set_ylabel('Y')
        plt.colorbar(im, ax=axes[row, col])
    
    # 마지막 subplot 숨기기
    if array.shape[3] < 6:
        axes[1, 2].axis('off')
    
    plt.tight_layout()
    
    # visualize 폴더에 저장
    output_file = os.path.join(output_dir, f'{material_name.lower()}_fluence_map.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ 이미지 저장됨: {output_file}")
    
    plt.close()
    return output_file

def analyze_optical_properties(array, material_name, material_dir):
    """광학 특성 분석"""
    print(f"\n=== {material_name} 광학 특성 분석 ===")
    
    # Fluence Map 통계
    print(f"Fluence Map 통계:")
    print(f"  최대값: {np.max(array):.6f}")
    print(f"  최소값: {np.min(array):.6f}")
    print(f"  평균값: {np.mean(array):.6f}")
    print(f"  표준편차: {np.std(array):.6f}")
    
    # 시간 게이트별 분석
    print(f"시간 게이트별 분석:")
    for t in range(array.shape[3]):
        time_slice = array[:, :, :, t]
        print(f"  게이트 {t+1}: 최대={np.max(time_slice):.6f}, 평균={np.mean(time_slice):.6f}")
    
    # 시뮬레이션 설정 파일에서 정보 가져오기
    try:
        config_file = os.path.join(material_dir, f'{material_name.lower()}_simulation.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"시뮬레이션 정보:")
            
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
            detp_file = os.path.join(material_dir, f'{material_name.lower()}_result_detp.jdat')
            if os.path.exists(detp_file):
                with open(detp_file, 'r') as f:
                    detp_data = json.load(f)
                if 'DetectedPhoton' in detp_data:
                    detected = detp_data['DetectedPhoton']
                    print(f"  검출된 광자: {detected:,}")
                    if 'Session' in config and 'Photons' in config['Session']:
                        print(f"  검출률: {detected/total_photons*100:.3f}%")
        else:
            print(f"시뮬레이션 정보: 설정 파일을 찾을 수 없음")
    except Exception as e:
        print(f"시뮬레이션 정보 분석 중 오류: {e}")

def create_comparison_visualization(arrays, materials, output_dir):
    """모든 매질 비교 시각화"""
    print("\n=== 모든 매질 비교 시각화 ===")
    
    # 모든 Time Gate 정규화
    gate_ranges = []
    for gate_idx in range(5):
        gate_values = []
        for array in arrays:
            gate_slice = array[:, :, :, gate_idx]
            gate_values.append(gate_slice)
        
        all_gate_values = np.concatenate([arr.flatten() for arr in gate_values])
        gate_min = np.min(all_gate_values)
        gate_max = np.max(all_gate_values)
        gate_ranges.append((gate_min, gate_max))
        print(f"Gate {gate_idx + 1} 정규화 범위: {gate_min:.6f} ~ {gate_max:.6f}")
    
    # 3개 매질, 5개 Time Gate로 구성된 플롯
    fig, axes = plt.subplots(3, 5, figsize=(20, 12))
    fig.suptitle('Material Comparison - All Gates Normalized', fontsize=16)
    
    for i, (array, material) in enumerate(zip(arrays, materials)):
        for j in range(5):  # 5개 Time Gate
            # 중간 z-슬라이스 시각화
            z_slice = array.shape[2] // 2
            
            # 각 Gate별 정규화된 스케일 사용
            gate_min, gate_max = gate_ranges[j]
            im = axes[i, j].imshow(array[:, :, z_slice, j], cmap='hot', origin='lower',
                                 vmin=gate_min, vmax=gate_max)
            axes[i, j].set_title(f'{material} - Gate {j+1} (Normalized)')
            
            axes[i, j].set_xlabel('X')
            axes[i, j].set_ylabel('Y')
            plt.colorbar(im, ax=axes[i, j])
    
    plt.tight_layout()
    
    # visualize 폴더에 저장
    output_file = os.path.join(output_dir, 'material_comparison.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ 비교 이미지 저장됨: {output_file}")
    
    plt.close()
    return output_file

def main():
    """메인 함수"""
    print("=== 모든 매질 시각화 실행 ===")
    
    # 출력 디렉토리 생성
    output_dir = "visualize"
    os.makedirs(output_dir, exist_ok=True)
    print(f"출력 디렉토리: {output_dir}")
    
    # 매질 설정
    materials = ['Air', 'Water', 'Glass']
    material_dirs = ['air', 'water', 'glass']
    jnii_files = ['air/air_result.jnii', 'water/water_result.jnii', 'glass/glass_result.jnii']
    
    # 모든 매질의 데이터 로드
    arrays = []
    generated_files = []
    
    for i, (material, material_dir, jnii_file) in enumerate(zip(materials, material_dirs, jnii_files)):
        print(f"\n{'='*50}")
        print(f"{material} 매질 데이터 로드 중...")
        print(f"{'='*50}")
        
        if os.path.exists(jnii_file):
            try:
                # 이미지 데이터 추출
                array, metadata = extract_jnifti_data(jnii_file)
                arrays.append(array)
                print(f"✅ {material} 데이터 로드 완료")
                
            except Exception as e:
                print(f"❌ {material} 데이터 로드 실패: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ 파일을 찾을 수 없음: {jnii_file}")
    
    # 모든 Time Gate 정규화 범위 계산
    if len(arrays) >= 2:
        print(f"\n{'='*50}")
        print("모든 Time Gate 정규화 범위 계산")
        print(f"{'='*50}")
        
        gate_ranges = []
        for gate_idx in range(5):
            gate_values = []
            for array in arrays:
                gate_slice = array[:, :, :, gate_idx]
                gate_values.append(gate_slice)
            
            all_gate_values = np.concatenate([arr.flatten() for arr in gate_values])
            gate_min = np.min(all_gate_values)
            gate_max = np.max(all_gate_values)
            gate_ranges.append((gate_min, gate_max))
            print(f"Gate {gate_idx + 1} 정규화 범위: {gate_min:.6f} ~ {gate_max:.6f}")
    else:
        gate_ranges = None
    
    # 개별 매질 시각화 (정규화된 스케일 사용)
    for i, (material, material_dir, array) in enumerate(zip(materials, material_dirs, arrays)):
        print(f"\n{'='*50}")
        print(f"{material} 매질 시각화 중...")
        print(f"{'='*50}")
        
        try:
            # 개별 시각화 (정규화된 스케일)
            output_file = visualize_fluence_map(array, output_dir, material, gate_ranges)
            generated_files.append(output_file)
            
            # 특성 분석
            analyze_optical_properties(array, material, material_dir)
            
            print(f"✅ {material} 시각화 완료")
            
        except Exception as e:
            print(f"❌ {material} 시각화 실패: {e}")
            import traceback
            traceback.print_exc()
    
    # 모든 매질 비교 시각화
    if len(arrays) >= 2:
        print(f"\n{'='*50}")
        print("모든 매질 비교 시각화")
        print(f"{'='*50}")
        
        try:
            comparison_file = create_comparison_visualization(arrays, materials, output_dir)
            generated_files.append(comparison_file)
        except Exception as e:
            print(f"❌ 비교 시각화 실패: {e}")
    
    # 결과 요약
    print(f"\n{'='*50}")
    print("시각화 완료 요약")
    print(f"{'='*50}")
    print(f"생성된 파일들 ({len(generated_files)}개):")
    for file in generated_files:
        print(f"  ✅ {file}")
    
    print(f"\n모든 시각화 파일이 '{output_dir}/' 폴더에 저장되었습니다!")

if __name__ == "__main__":
    main()
