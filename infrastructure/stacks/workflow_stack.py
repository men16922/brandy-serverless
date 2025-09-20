"""
Workflow Stack - Step Functions state machines
"""

from aws_cdk import (
    Stack,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class WorkflowStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, api_stack, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.api_stack = api_stack
        self.environment = environment
        
        # Express workflow for parallel image generation
        self.express_workflow = self._create_express_workflow()
        
        # Standard workflow for user input waiting
        self.standard_workflow = self._create_standard_workflow()
    
    def _create_express_workflow(self) -> sfn.StateMachine:
        """Create Express workflow for parallel image generation"""
        
        # Parallel image generation tasks
        dalle_task = tasks.LambdaInvoke(
            self, "DalleImageGeneration",
            lambda_function=self.api_stack.image_generator,
            payload=sfn.TaskInput.from_object({
                "provider": "dalle",
                "sessionId.$": "$.sessionId",
                "prompt.$": "$.prompt",
                "style.$": "$.style"
            }),
            timeout=Duration.seconds(30)
        )
        
        sdxl_task = tasks.LambdaInvoke(
            self, "SdxlImageGeneration", 
            lambda_function=self.api_stack.image_generator,
            payload=sfn.TaskInput.from_object({
                "provider": "sdxl",
                "sessionId.$": "$.sessionId", 
                "prompt.$": "$.prompt",
                "style.$": "$.style"
            }),
            timeout=Duration.seconds(30)
        )
        
        gemini_task = tasks.LambdaInvoke(
            self, "GeminiImageGeneration",
            lambda_function=self.api_stack.image_generator,
            payload=sfn.TaskInput.from_object({
                "provider": "gemini",
                "sessionId.$": "$.sessionId",
                "prompt.$": "$.prompt", 
                "style.$": "$.style"
            }),
            timeout=Duration.seconds(30)
        )
        
        # Parallel execution
        parallel_generation = sfn.Parallel(
            self, "ParallelImageGeneration",
            comment="Generate images using multiple AI providers in parallel"
        )
        
        parallel_generation.branch(dalle_task)
        parallel_generation.branch(sdxl_task) 
        parallel_generation.branch(gemini_task)
        
        # Express state machine
        return sfn.StateMachine(
            self, "ExpressWorkflow",
            state_machine_name=f"branding-chatbot-express-{self.environment}",
            definition=parallel_generation,
            state_machine_type=sfn.StateMachineType.EXPRESS,
            timeout=Duration.minutes(5)
        )
    
    def _create_standard_workflow(self) -> sfn.StateMachine:
        """Create Standard workflow for user input waiting"""
        
        # Wait for user selection task
        wait_for_selection = sfn.Wait(
            self, "WaitForUserSelection",
            time=sfn.WaitTime.duration(Duration.seconds(30))
        )
        
        # Check selection status
        check_selection = tasks.LambdaInvoke(
            self, "CheckSelectionStatus",
            lambda_function=self.api_stack.session_manager,
            payload=sfn.TaskInput.from_object({
                "action": "checkSelection",
                "sessionId.$": "$.sessionId",
                "step.$": "$.step"
            })
        )
        
        # Choice state for selection status
        selection_choice = sfn.Choice(self, "SelectionChoice")
        
        # Continue to next step if selection made
        continue_workflow = sfn.Pass(
            self, "ContinueWorkflow",
            comment="User has made selection, continue to next step"
        )
        
        # Define workflow
        definition = wait_for_selection.next(
            check_selection.next(
                selection_choice
                .when(
                    sfn.Condition.string_equals("$.Payload.status", "selected"),
                    continue_workflow
                )
                .otherwise(wait_for_selection)
            )
        )
        
        # Standard state machine
        return sfn.StateMachine(
            self, "StandardWorkflow", 
            state_machine_name=f"branding-chatbot-standard-{self.environment}",
            definition=definition,
            state_machine_type=sfn.StateMachineType.STANDARD,
            timeout=Duration.hours(24)
        )