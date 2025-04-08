from .llm_controller import LLMController
from .abs.robot_wrapper import RobotType
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(CURRENT_DIR, './assets/attack/harm_instructs.txt'), 'r') as f:
    harm_instructs = f.read().split("\n---\n")


controller = LLMController(task='attack', robot_type=RobotType.VIRTUAL, use_http=False)


for ins in harm_instructs:
    ins = "[A] " + ins.split('Output:\n')[-1]
    controller.execute_task_description(ins)

controller.get_asr()

