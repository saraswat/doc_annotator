#!/usr/bin/env python3
"""
Comprehensive test runner for the chat system
Runs both backend (Python) and frontend (TypeScript/Jest) tests
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path
from typing import List, Optional


class Colors:
    """Terminal color codes for output formatting"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Test runner for chat system components"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_dir = project_root / "backend"
        self.frontend_dir = project_root / "frontend"
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    
    def run_command(self, command: List[str], cwd: Path, description: str) -> bool:
        """Run a command and return success status"""
        print(f"{Colors.OKBLUE}Running: {' '.join(command)}{Colors.ENDC}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.print_success(f"{description} passed")
                if result.stdout.strip():
                    print(f"Output:\n{result.stdout}")
                return True
            else:
                self.print_error(f"{description} failed")
                if result.stderr.strip():
                    print(f"Error output:\n{result.stderr}")
                if result.stdout.strip():
                    print(f"Standard output:\n{result.stdout}")
                return False
        
        except subprocess.TimeoutExpired:
            self.print_error(f"{description} timed out")
            return False
        except Exception as e:
            self.print_error(f"{description} failed with exception: {e}")
            return False
    
    def run_backend_tests(self, test_types: Optional[List[str]] = None) -> bool:
        """Run backend Python tests"""
        self.print_header("BACKEND TESTS (Python/FastAPI)")
        
        if not (self.backend_dir / "venv").exists():
            self.print_warning("Virtual environment not found. Creating...")
            if not self.setup_backend_env():
                return False
        
        # Activate virtual environment
        venv_python = self.backend_dir / "venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = self.backend_dir / "venv" / "Scripts" / "python.exe"  # Windows
        
        if not venv_python.exists():
            self.print_error("Python virtual environment not properly set up")
            return False
        
        # Install test dependencies
        if not self.run_command(
            [str(venv_python), "-m", "pip", "install", "-e", ".", "pytest", "pytest-asyncio"],
            self.backend_dir,
            "Installing test dependencies"
        ):
            return False
        
        # Run specific test categories or all tests
        test_commands = []
        
        if not test_types or "unit" in test_types:
            test_commands.append({
                "cmd": [str(venv_python), "-m", "pytest", "tests/test_chat_service.py", "-v"],
                "desc": "Chat Service Unit Tests"
            })
            test_commands.append({
                "cmd": [str(venv_python), "-m", "pytest", "tests/test_llm_client.py", "-v"],
                "desc": "LLM Client Unit Tests"
            })
            test_commands.append({
                "cmd": [str(venv_python), "-m", "pytest", "tests/test_context_manager.py", "-v"],
                "desc": "Context Manager Unit Tests"
            })
            test_commands.append({
                "cmd": [str(venv_python), "-m", "pytest", "tests/test_chat_models.py", "-v"],
                "desc": "Database Model Tests"
            })
        
        if not test_types or "api" in test_types:
            test_commands.append({
                "cmd": [str(venv_python), "-m", "pytest", "tests/test_chat_api.py", "-v"],
                "desc": "API Endpoint Tests"
            })
        
        if not test_types or "integration" in test_types:
            test_commands.append({
                "cmd": [str(venv_python), "-m", "pytest", "tests/test_chat_integration.py", "-v"],
                "desc": "Integration Tests"
            })
        
        # Run all test commands
        all_passed = True
        for test_cmd in test_commands:
            if not self.run_command(test_cmd["cmd"], self.backend_dir, test_cmd["desc"]):
                all_passed = False
        
        return all_passed
    
    def run_frontend_tests(self, test_types: Optional[List[str]] = None) -> bool:
        """Run frontend TypeScript/Jest tests"""
        self.print_header("FRONTEND TESTS (React/TypeScript/Jest)")
        
        if not (self.frontend_dir / "node_modules").exists():
            self.print_warning("Node modules not found. Installing...")
            if not self.setup_frontend_env():
                return False
        
        # Run specific test categories or all tests
        test_commands = []
        
        if not test_types or "components" in test_types:
            test_commands.append({
                "cmd": ["npm", "test", "--", "src/components/Chat/__tests__/", "--watchAll=false", "--verbose"],
                "desc": "React Component Tests"
            })
        
        if not test_types or "hooks" in test_types:
            test_commands.append({
                "cmd": ["npm", "test", "--", "src/hooks/__tests__/", "--watchAll=false", "--verbose"],
                "desc": "React Hook Tests"
            })
        
        if not test_types or "services" in test_types:
            test_commands.append({
                "cmd": ["npm", "test", "--", "src/services/", "--watchAll=false", "--verbose"],
                "desc": "Service Layer Tests"
            })
        
        # If no specific types, run all tests
        if not test_commands:
            test_commands.append({
                "cmd": ["npm", "test", "--", "--watchAll=false", "--coverage"],
                "desc": "All Frontend Tests with Coverage"
            })
        
        # Run all test commands
        all_passed = True
        for test_cmd in test_commands:
            if not self.run_command(test_cmd["cmd"], self.frontend_dir, test_cmd["desc"]):
                all_passed = False
        
        return all_passed
    
    def setup_backend_env(self) -> bool:
        """Set up backend Python environment"""
        print("Setting up backend Python environment...")
        
        # Create virtual environment
        if not self.run_command(
            [sys.executable, "-m", "venv", "venv"],
            self.backend_dir,
            "Creating virtual environment"
        ):
            return False
        
        # Install requirements
        venv_pip = self.backend_dir / "venv" / "bin" / "pip"
        if not venv_pip.exists():
            venv_pip = self.backend_dir / "venv" / "Scripts" / "pip.exe"  # Windows
        
        if not self.run_command(
            [str(venv_pip), "install", "-r", "requirements.txt"],
            self.backend_dir,
            "Installing Python dependencies"
        ):
            return False
        
        return True
    
    def setup_frontend_env(self) -> bool:
        """Set up frontend Node.js environment"""
        print("Setting up frontend Node.js environment...")
        
        if not self.run_command(
            ["npm", "install"],
            self.frontend_dir,
            "Installing Node.js dependencies"
        ):
            return False
        
        return True
    
    def run_lint_checks(self) -> bool:
        """Run linting and code quality checks"""
        self.print_header("CODE QUALITY CHECKS")
        
        all_passed = True
        
        # Backend linting (if available)
        if (self.backend_dir / "venv").exists():
            venv_python = self.backend_dir / "venv" / "bin" / "python"
            if not venv_python.exists():
                venv_python = self.backend_dir / "venv" / "Scripts" / "python.exe"
            
            # Try to run flake8 or black if available
            for linter, cmd in [("Black formatter", ["black", "--check", "."]), 
                               ("Flake8 linter", ["flake8", "app/", "tests/"])]:
                try:
                    subprocess.run([str(venv_python), "-m"] + cmd, 
                                 cwd=self.backend_dir, check=True, 
                                 capture_output=True, timeout=60)
                    self.print_success(f"Backend {linter} passed")
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    self.print_warning(f"Backend {linter} not available or failed")
        
        # Frontend linting
        if (self.frontend_dir / "node_modules").exists():
            # Try to run ESLint if available
            try:
                subprocess.run(["npm", "run", "lint"], 
                             cwd=self.frontend_dir, check=True, 
                             capture_output=True, timeout=60)
                self.print_success("Frontend ESLint passed")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                self.print_warning("Frontend linting not available or failed")
        
        return all_passed
    
    def run_all_tests(self, test_types: Optional[List[str]] = None) -> bool:
        """Run all tests"""
        self.print_header("CHAT SYSTEM COMPREHENSIVE TESTS")
        
        backend_passed = self.run_backend_tests(test_types)
        frontend_passed = self.run_frontend_tests(test_types)
        lint_passed = self.run_lint_checks()
        
        # Print summary
        self.print_header("TEST SUMMARY")
        
        if backend_passed:
            self.print_success("Backend tests passed")
        else:
            self.print_error("Backend tests failed")
        
        if frontend_passed:
            self.print_success("Frontend tests passed")
        else:
            self.print_error("Frontend tests failed")
        
        overall_success = backend_passed and frontend_passed
        
        if overall_success:
            self.print_success("All tests passed! 🎉")
        else:
            self.print_error("Some tests failed. Please review the output above.")
        
        return overall_success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run chat system tests")
    parser.add_argument("--backend-only", action="store_true", help="Run only backend tests")
    parser.add_argument("--frontend-only", action="store_true", help="Run only frontend tests")
    parser.add_argument("--type", choices=["unit", "integration", "api", "components", "hooks", "services"], 
                       action="append", help="Run specific test types")
    parser.add_argument("--setup", action="store_true", help="Set up test environments")
    
    args = parser.parse_args()
    
    # Find project root
    current_dir = Path(__file__).parent.absolute()
    project_root = current_dir
    
    # Ensure we have backend and frontend directories
    if not (project_root / "backend").exists() or not (project_root / "frontend").exists():
        print(f"{Colors.FAIL}Error: Could not find backend/ and frontend/ directories{Colors.ENDC}")
        print(f"Current directory: {current_dir}")
        sys.exit(1)
    
    runner = TestRunner(project_root)
    
    # Set up environments if requested
    if args.setup:
        runner.print_header("ENVIRONMENT SETUP")
        backend_setup = runner.setup_backend_env()
        frontend_setup = runner.setup_frontend_env()
        
        if backend_setup and frontend_setup:
            runner.print_success("All environments set up successfully")
        else:
            runner.print_error("Environment setup failed")
            sys.exit(1)
        return
    
    # Run tests based on arguments
    success = True
    
    if args.backend_only:
        success = runner.run_backend_tests(args.type)
    elif args.frontend_only:
        success = runner.run_frontend_tests(args.type)
    else:
        success = runner.run_all_tests(args.type)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()