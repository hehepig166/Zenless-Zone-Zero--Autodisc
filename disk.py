import json

# 宏定义变量
PLAYER_KEY = "player"
EQUIPMENT_KEY = "equipment"
INITIAL_STATS_KEY = "initial_stats"
EVALUATION_CONSTRAINTS_KEY = "constraints"
STAT_CONSTRAINTS_KEY = "stat_constraints"
SET_CONSTRAINTS_KEY = "set_constraints"
STATS_KEY = "stats"
BASIC_STATS_KEY = "basic_stats"
SLOT_KEY = "slot"
SET_KEY = "set"
NAME_KEY = "name"
TOSHOW_KEY = "stats_to_show"

# 百分比加成的标识符
PERCENTAGE_SUFFIX = "@"

# 音擎的 slot_id 是 0
SLOT_ID_ENGINE = 0


class EquipmentOptimizer:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config_data = self.load_config(config_file)
        self.player_stats = self.config_data[PLAYER_KEY][INITIAL_STATS_KEY]
        self.equipment = self.config_data[EQUIPMENT_KEY]
        self.evaluation_constraints = self.config_data[EVALUATION_CONSTRAINTS_KEY]
        self.stats_to_show = self.config_data.get(TOSHOW_KEY, [])

        # 预处理装备，按槽位编号进行索引
        self.max_slot_id = max(eq[SLOT_KEY] for eq in self.equipment)
        self.equipment_by_slot = self.index_equipment_by_slot(self.equipment)
    
    def handle_error(self, msg):
        print(msg)
        exit(-1)

    def load_config(self, file_path):
        """加载配置文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def index_equipment_by_slot(self, equipment):
        """按槽位编号索引装备"""
        equipment_by_slot = {i: [] for i in range(self.max_slot_id + 1)}
        for eq in equipment:
            slot = eq[SLOT_KEY]
            if slot in equipment_by_slot:
                equipment_by_slot[slot].append(eq)
        return equipment_by_slot

    def calculate_final_stats(self, selected_equipment):
        """计算搭配后的最终属性"""
        
        base_stats = self.player_stats.copy()
        # 先计算（音擎带来的）基础属性加成
        for eq in selected_equipment:
            if BASIC_STATS_KEY not in eq:
                continue
            for stat, value in eq[BASIC_STATS_KEY].items():
                # 因为驱动盘主词条可能和副词条重名，所以重名的时候主词条开头加个 _ 以便 json 能正确识别两个词条。这里将词条开头的 _ 删除。
                stat = stat.lstrip('_')
                if stat.endswith(PERCENTAGE_SUFFIX):
                    # 百分比加成：需要乘以基础属性值
                    stat_n = stat.replace(PERCENTAGE_SUFFIX, "")
                    if stat_n in self.player_stats:
                        base_stats[stat_n] += self.player_stats[stat_n] * value / 100
                    else:
                        self.handle_error(f'[{eq[NAME_KEY]}] err: need initial stat value of \'{stat_n}\'')
                else:
                    base_stats[stat] = base_stats.get(stat, 0) + value

        total_stats = base_stats.copy()
        # 计算每个驱动盘带来的属性加成
        for eq in selected_equipment:
            for stat, value in eq[STATS_KEY].items():
                # 因为驱动盘主词条可能和副词条重名，所以重名的时候主词条开头加个 _ 以便 json 能正确识别两个词条。这里将词条开头的 _ 删除。
                stat = stat.lstrip('_')
                if stat.endswith(PERCENTAGE_SUFFIX):
                    # 百分比加成：需要乘以基础属性值
                    stat_n = stat.replace(PERCENTAGE_SUFFIX, "")
                    if stat_n in base_stats:
                        total_stats[stat_n] += base_stats[stat_n] * value / 100
                    else:
                        self.handle_error(f'[{eq[NAME_KEY]}] err: need initial stat value of \'{stat_n}\'')
                else:
                    total_stats[stat] = total_stats.get(stat, 0) + value
        
        return total_stats
    
    def check_stat_constraints(self, total_stats):
        """检查属性约束是否满足"""
        for stat, condition in self.evaluation_constraints[STAT_CONSTRAINTS_KEY].items():
            stat_value = total_stats.get(stat, 0)
            if condition.startswith(">="):
                if stat_value < float(condition[2:]):
                    return False
            elif condition.startswith("<="):
                if stat_value > float(condition[2:]):
                    return False
            elif condition.startswith(">"):
                if stat_value <= float(condition[1:]):
                    return False
            elif condition.startswith("<"):
                if stat_value >= float(condition[1:]):
                    return False
        return True
    
    def check_set_constraints(self, selected_equipment):
        """检查套装约束是否满足"""
        set_count = {}
        for eq in selected_equipment:
            set_count[eq[SET_KEY]] = set_count.get(eq[SET_KEY], 0) + 1
        
        # print('@@@set_count:', set_count)

        for set_name, min_count in self.evaluation_constraints[SET_CONSTRAINTS_KEY].items():
            if set_count.get(set_name, 0) < min_count:
                return False
        
        return True

    def evaluate(self, selected_equipment):
        """评估选择的装备组合是否符合约束条件"""
        total_stats = self.calculate_final_stats(selected_equipment)
        
        # print('-------- eval start')
        # print(selected_equipment)
        # print(total_stats)

        # 检查属性约束
        if not self.check_stat_constraints(total_stats):
            return False
        
        # print('[] stat constraints pass')

        # 检查套装约束
        if not self.check_set_constraints(selected_equipment):
            return False
        
        # print('[[]] set_constraints pass')

        return True
    
    def generate_combinations(self):
        """生成符合约束的组合"""
        valid_combinations = []
        
        def generate_slot_combinations(slot_idx, current_combination):
            """递归生成每个槽位的所有组合"""
            if slot_idx > self.max_slot_id:  # 如果已经遍历完了所有槽位
                if self.evaluate(current_combination):
                    valid_combinations.append(current_combination)
                return
            
            # 获取当前槽位可能的装备
            possible_equipment = self.equipment_by_slot.get(slot_idx, [])
            if possible_equipment:
                for eq in possible_equipment:
                    generate_slot_combinations(slot_idx + 1, current_combination + [eq])
            else:
                # 当前槽位无装备
                generate_slot_combinations(slot_idx + 1, current_combination)
        
        # 从槽位 0 开始递归生成装备组合
        generate_slot_combinations(0, [])
        
        return valid_combinations


    def get_stats_to_show(self):
        ret = self.stats_to_show.copy()
        for stat, condition in self.evaluation_constraints[STAT_CONSTRAINTS_KEY].items():
            if stat not in ret:
                ret.append(stat)
        return ret
        

    def print_all_drive_dics(self):
        print(self.equipment_by_slot)