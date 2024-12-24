import json
import sys
import time
from disk import EquipmentOptimizer


def main():

    # 默认配置文件路径
    config_file = 'config.json'

    # 检查命令行参数数量
    if len(sys.argv) < 2:
        print('Usage: python main.py <config_file>')
        print('using default configpath (config.json)')
    else:
        config_file = sys.argv[1]
        print(f'using given configpath ({config_file})')
    

    # 创建 EquipmentOptimizer 实例
    optimizer = EquipmentOptimizer(config_file)
    
    # 记录开始时间
    start_time = time.time()

    # 生成符合约束的所有装备搭配方案
    valid_combinations = optimizer.generate_combinations()
    
    # 记录结束时间
    end_time = time.time()

    # 计算搜索所花费的时间
    elapsed_time = end_time - start_time
    print(f"Search completed in {elapsed_time:.4f} seconds")

    # 打印所有有效的搭配方案
    print(f"found {len(valid_combinations)} valid combinations :")
    
    # 设置要显示的属性列表
    to_show_stat = optimizer.get_stats_to_show()

    for idx, combination in enumerate(valid_combinations, 1):
        print(f"\n[combination {idx}]")

        # 打印装备信息
        for eq in combination:
            print(f"  eq: \'{eq['name']}\', slot: {eq['slot']}, set: \'{eq['set']}\', stats: {eq['stats']}")
            #print(f"  eq: \'{eq['name']}\', slot: {eq['slot']}, set: \'{eq['set']}\'")
        
        # 计算并显示最终属性
        final_stats = optimizer.calculate_final_stats(combination)
        print("  final stats:")
        for stat in to_show_stat:
            if stat in final_stats:
                print(f"    {stat}: {final_stats[stat]:.2f}")
            else:
                print(f"    {stat}: N/A")
        
    
if __name__ == '__main__':
    main()
