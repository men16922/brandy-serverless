#!/usr/bin/env python3
"""
Python-based Integration Test Runner
Provides flexible test execution for local and AWS dev environments
"""

import os
import sys
import subprocess
import time
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

class IntegrationTestRunner:
    """Manages integration test execution across environments"""
    
    def __init__(self, environment: str = 'local'):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / 'venv'
        self.compose_file = self.project_root / 'docker-compose.local.yml'
        self.test_results = []
        
    def print_header(self, message: str):
        """Print formatted header"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
        print(f"{Colors.BLUE}{message}{Colors.NC}")
        print(f"{Colors.BLUE}{'='*60}{Colors.NC}\n")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {message}{Colors.NC}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}❌ {message}{Colors.NC}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ {message}{Colors.NC}")
    
    def check_docker_services(self) -> bool:
        """Check if Docker services are available"""
        self.print_info("Checking Docker services...")
        
        try:
            # Check if Docker is installed
            subprocess.run(['docker', '--version'], 
                         capture_output=True, check=True)
            
            # Check if Docker daemon is running
            subprocess.run(['docker', 'info'], 
                         capture_output=True, check=True)
            
            self.print_success("Docker is available")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_error("Docker not available")
            return False
    
    def start_docker_services(self) -> bool:
        """Start Docker Compose services"""
        self.print_info("Starting Docker Compose services...")
        
        try:
            # Start services
            subprocess.run(
                ['docker-compose', '-f', str(self.compose_file), 'up', '-d'],
                check=True,
                capture_output=True
            )
            
            self.print_info("Waiting for services to be healthy...")
            time.sleep(10)
            
            # Check service health
            services_healthy = True
            
            # Check DynamoDB Local
            try:
                requests.get('http://localhost:8000', timeout=5)
                self.print_success("DynamoDB Local is running (port 8000)")
            except:
                self.print_error("DynamoDB Local not responding")
                services_healthy = False
            
            # Check MinIO
            try:
                requests.get('http://localhost:9000/minio/health/live', timeout=5)
                self.print_success("MinIO is running (port 9000)")
            except:
                self.print_error("MinIO not responding")
                services_healthy = False
            
            # Check Chroma
            try:
                requests.get('http://localhost:8001', timeout=5)
                self.print_success("Chroma is running (port 8001)")
            except:
                self.print_error("Chroma not responding")
                services_healthy = False
            
            # Check DynamoDB Admin UI (non-critical)
            try:
                requests.get('http://localhost:8002', timeout=5)
                self.print_success("DynamoDB Admin UI is running (port 8002)")
            except:
                self.print_warning("DynamoDB Admin UI not responding (non-critical)")
            
            if services_healthy:
                print()
                self.print_success("All Docker services are healthy")
                print()
            
            return services_healthy
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to start Docker services: {e}")
            return False
    
    def setup_local_environment(self):
        """Setup environment variables for local testing"""
        os.environ['ENVIRONMENT'] = 'local'
        os.environ['DYNAMODB_ENDPOINT'] = 'http://localhost:8000'
        os.environ['S3_ENDPOINT'] = 'http://localhost:9000'
        os.environ['CHROMA_ENDPOINT'] = 'http://localhost:8001'
        os.environ['SESSIONS_TABLE'] = 'branding-chatbot-sessions-test'
        os.environ['S3_BUCKET'] = 'branding-chatbot-assets-test'
        os.environ['AWS_ACCESS_KEY_ID'] = 'dummy'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'dummy'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        
        self.print_success("Local environment configured")
    
    def setup_aws_dev_environment(self):
        """Setup environment variables for AWS dev testing"""
        # Check AWS credentials
        if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
            self.print_error("AWS credentials not found")
            self.print_warning("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            return False
        
        self.print_success("AWS credentials found")
        
        os.environ['ENVIRONMENT'] = 'dev'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        os.environ['SESSIONS_TABLE'] = 'ai-branding-chatbot-sessions'
        os.environ['S3_BUCKET'] = 'ai-branding-chatbot-assets'
        os.environ['BEDROCK_REGION'] = 'us-east-1'
        os.environ['ENABLE_FALLBACK'] = 'false'  # Use Bedrock only in dev
        
        self.print_success("AWS dev environment configured")
        return True
    
    def run_pytest(self, test_path: Optional[str] = None, verbose: bool = True) -> int:
        """Run pytest with specified configuration"""
        python_path = self.venv_path / 'bin' / 'python'
        
        if not python_path.exists():
            self.print_error(f"Python not found at {python_path}")
            return 1
        
        # Build pytest command
        cmd = [
            str(python_path),
            '-m', 'pytest',
            test_path or 'tests/integration/test_hackathon_workflow.py',
            '-v' if verbose else '',
            '--tb=short',
            '--color=yes'
        ]
        
        # Remove empty strings
        cmd = [c for c in cmd if c]
        
        self.print_info(f"Running: {' '.join(cmd)}")
        print()
        
        # Run tests
        result = subprocess.run(cmd, cwd=self.project_root)
        
        return result.returncode
    
    def run_local_tests(self) -> int:
        """Run all local integration tests"""
        self.print_header("Running LOCAL Integration Tests")
        
        # Check and start Docker services
        if not self.check_docker_services():
            return 1
        
        if not self.start_docker_services():
            return 1
        
        # Setup environment
        self.setup_local_environment()
        
        # Run tests
        self.print_info("Running integration tests...")
        print()
        
        exit_code = self.run_pytest()
        
        print()
        if exit_code == 0:
            self.print_success("All local tests passed!")
            print()
            self.print_info("Verification URLs:")
            print(f"  • DynamoDB Admin: {Colors.GREEN}http://localhost:8002{Colors.NC}")
            print(f"  • MinIO Console: {Colors.GREEN}http://localhost:9001{Colors.NC} (minioadmin/minioadmin)")
            print(f"  • Chroma API: {Colors.GREEN}http://localhost:8001{Colors.NC}")
        else:
            self.print_error("Some tests failed")
        
        return exit_code
    
    def run_aws_dev_tests(self) -> int:
        """Run all AWS dev integration tests"""
        self.print_header("Running AWS DEV Integration Tests")
        
        # Setup environment
        if not self.setup_aws_dev_environment():
            return 1
        
        # Check SAM stack deployment
        self.print_info("Checking SAM stack deployment...")
        
        try:
            result = subprocess.run(
                ['aws', 'cloudformation', 'describe-stacks',
                 '--stack-name', 'branding-chatbot',
                 '--region', 'us-east-1'],
                capture_output=True,
                check=True
            )
            
            self.print_success("SAM stack 'branding-chatbot' is deployed")
            
            # Try to get API URL
            try:
                stack_info = json.loads(result.stdout)
                outputs = stack_info['Stacks'][0].get('Outputs', [])
                api_url = next(
                    (o['OutputValue'] for o in outputs if o['OutputKey'] == 'ApiUrl'),
                    None
                )
                
                if api_url:
                    self.print_success(f"API Gateway URL: {api_url}")
                    os.environ['API_BASE_URL'] = api_url
            except:
                pass
                
        except subprocess.CalledProcessError:
            self.print_warning("SAM stack not found. Some tests may be skipped.")
        
        print()
        
        # Run tests
        self.print_info("Running AWS dev integration tests...")
        print()
        
        exit_code = self.run_pytest()
        
        print()
        if exit_code == 0:
            self.print_success("All AWS dev tests passed!")
            print()
            self.print_info("AWS Resources:")
            print(f"  • DynamoDB Table: {Colors.GREEN}{os.getenv('SESSIONS_TABLE')}{Colors.NC}")
            print(f"  • S3 Bucket: {Colors.GREEN}{os.getenv('S3_BUCKET')}{Colors.NC}")
            print(f"  • Region: {Colors.GREEN}{os.getenv('AWS_DEFAULT_REGION')}{Colors.NC}")
        else:
            self.print_error("Some tests failed")
        
        return exit_code
    
    def run_specific_test(self, test_name: str) -> int:
        """Run a specific test"""
        self.print_header(f"Running Specific Test: {test_name}")
        
        # Setup environment based on self.environment
        if self.environment == 'local':
            if not self.check_docker_services() or not self.start_docker_services():
                return 1
            self.setup_local_environment()
        else:
            if not self.setup_aws_dev_environment():
                return 1
        
        # Run specific test
        test_path = f"tests/integration/test_hackathon_workflow.py::{test_name}"
        exit_code = self.run_pytest(test_path, verbose=True)
        
        return exit_code
    
    def list_tests(self):
        """List all available tests"""
        self.print_header("Available Integration Tests")
        
        tests = [
            ("TestFullWorkflowWithBedrock", "Complete 5-step workflow with Bedrock"),
            ("TestAutonomousExecution", "Autonomous agent execution"),
            ("TestFallbackMechanism", "Fallback to alternative providers"),
            ("TestPDFReportGeneration", "PDF report generation and storage"),
            ("TestConcurrentSessions", "Concurrent session handling"),
            ("TestWorkflowStateManagement", "Workflow pause and resume")
        ]
        
        for i, (test_name, description) in enumerate(tests, 1):
            print(f"  {i}. {Colors.GREEN}{test_name}{Colors.NC}")
            print(f"     {description}")
            print()
        
        print(f"{Colors.BLUE}Usage Examples:{Colors.NC}")
        print(f"  {Colors.YELLOW}python scripts/run_integration_tests.py local{Colors.NC}")
        print(f"  {Colors.YELLOW}python scripts/run_integration_tests.py dev{Colors.NC}")
        print(f"  {Colors.YELLOW}python scripts/run_integration_tests.py specific TestFullWorkflowWithBedrock{Colors.NC}")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run integration tests for AI Branding Chatbot'
    )
    
    parser.add_argument(
        'environment',
        choices=['local', 'dev', 'specific', 'list'],
        default='local',
        nargs='?',
        help='Test environment (default: local)'
    )
    
    parser.add_argument(
        'test_name',
        nargs='?',
        help='Specific test name (when environment=specific)'
    )
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner(args.environment)
    
    if args.environment == 'list':
        runner.list_tests()
        return 0
    
    if args.environment == 'local':
        return runner.run_local_tests()
    
    elif args.environment == 'dev':
        return runner.run_aws_dev_tests()
    
    elif args.environment == 'specific':
        if not args.test_name:
            runner.print_error("Please specify test name")
            runner.list_tests()
            return 1
        return runner.run_specific_test(args.test_name)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
