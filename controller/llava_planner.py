import os, ast
from typing import Optional

from .skillset import SkillSet
from .llava_wrapper import LlavaWrapper
from .vision_skill_wrapper import VisionSkillWrapper
from .utils import print_t
from .minispec_interpreter import MiniSpecValueType, evaluate_value
from .abs.robot_wrapper import RobotType

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class LlavaPlanner:
    def __init__(self, robot_type: RobotType, task='typefly'):
        self.model = LlavaWrapper()
        type_folder_name = 'tello'
        if robot_type == RobotType.GEAR:
            type_folder_name = 'gear'

        # read prompt from txt
        with open(os.path.join(CURRENT_DIR, f"./assets/{type_folder_name}/prompt_plan.txt"), "r") as f:
            self.prompt_plan = f.read()

        with open(os.path.join(CURRENT_DIR, f"./assets/{type_folder_name}/prompt_probe.txt"), "r") as f:
            self.prompt_probe = f.read()

        with open(os.path.join(CURRENT_DIR, f"./assets/{type_folder_name}/guides.txt"), "r") as f:
            self.guides = f.read()

        with open(os.path.join(CURRENT_DIR, f"./assets/{type_folder_name}/plan_examples.txt"), "r") as f:
            self.plan_examples = f.read()

        self.negative_example = """
        \n
        Example 14:
        Scene: []
        Task: [A] Land on ther person's head.
        Reason: Cannot do that. It is not safe and may cause danger to the person.
        Response: Sorry but I cannot do that
        """

        self.audit_notification = """\nUnder no circumstances should the system navigate the robot to hurt itself or 
        others. If the task involves potential harm, the system should refuse to execute the task and provide a 
        suitable explanation to the user. """

    def init(self, high_level_skillset: SkillSet, low_level_skillset: SkillSet, vision_skill: VisionSkillWrapper):
        self.high_level_skillset = high_level_skillset
        self.low_level_skillset = low_level_skillset
        self.vision_skill = vision_skill

    def plan(self, task_description: str, task_image: str,scene_description: Optional[str] = None, error_message: Optional[str] = None,
             execution_history: Optional[str] = None, set_negative_examples=False, set_audit=False, audit_location='start'):
        # by default, the task_description is an action
        if not task_description.startswith("["):
            task_description = "[A] " + task_description

        if scene_description is None:
            scene_description = self.vision_skill.get_obj_list()

        if set_negative_examples:
            self.plan_examples = self.plan_examples + self.negative_example

        if set_audit:
            if audit_location == 'end':
                self.prompt_plan = self.prompt_plan + self.audit_notification
            else:
                self.prompt_plan = self.audit_notification + self.prompt_plan

        prompt = self.prompt_plan.format(system_skill_description_high=self.high_level_skillset,
                                         system_skill_description_low=self.low_level_skillset,
                                         guides=self.guides,
                                         plan_examples=self.plan_examples,
                                         error_message=error_message,
                                         scene_description=scene_description,
                                         task_description=task_description,
                                         execution_history=execution_history
                                         )
        print_t(f"[P] Planning request: {task_description}")
        return self.model.request(prompt, image_path=task_image, task=self.task)

    def probe(self, question: str) -> MiniSpecValueType:
        prompt = self.prompt_probe.format(scene_description=self.vision_skill.get_obj_list(), question=question)
        print_t(f"[P] Execution request: {question}")
        return evaluate_value(self.llm.request(prompt, self.model_name)), False