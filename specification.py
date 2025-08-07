# main.py
from pydantic import BaseModel, Field
from typing import Optional


# Reusable value models
class TechnologyValue(BaseModel):
    """Defines the name and version of a technology."""
    name: Optional[str] = Field(description="The name of the technology, e.g., 'Java' or 'Spring Boot'.")
    version: Optional[str] = Field(description="The detected version of the technology, e.g., '17' or '3.2.0'.")


class CategoryWithValue(BaseModel):
    """A generic model for a category and its associated value object."""
    category: str = Field(description="The category of the analyzed item.")
    value: TechnologyValue


# --- Code Style Models ---
class NamingConventions(BaseModel):
    """Describes the coding naming conventions."""
    category: str = Field(description="Category for naming convention analysis.", default="naming")
    value: Optional[str] = Field(description="Description of the identified naming convention.")


class PackageStructure(BaseModel):
    """Describes the package or directory structure."""
    category: str = Field(description="Category for package structure analysis.", default="package_structure")
    value: Optional[str] = Field(description="Description of the package/directory organization.")


class CodeStyle(BaseModel):
    """Contains details about the project's code style."""
    naming_conventions: NamingConventions
    package_structure: PackageStructure


# --- Testing Models ---
class UnitTestsValue(BaseModel):
    """Value object for unit testing details."""
    framework: Optional[str] = Field(description="The unit testing framework used, e.g., 'JUnit 5'.")
    coverage: Optional[str] = Field(description="The method or tool used for code coverage, e.g., 'JaCoCo'.")


class UnitTests(BaseModel):
    """Contains all details about unit tests."""
    category: str = Field(description="Category for testing analysis.", default="testing")
    value: UnitTestsValue


class IntegrationTestsValue(BaseModel):
    """Value object for integration testing details."""
    framework: Optional[str] = Field(description="The integration testing framework used.")
    path: Optional[str] = Field(description="An example path to an integration test file.")


class IntegrationTests(BaseModel):
    """Contains all details about integration tests."""
    category: str = Field(description="Category for testing analysis.", default="testing")
    value: IntegrationTestsValue


class Testing(BaseModel):
    """Contains all details about the project's testing practices."""
    unit_tests: UnitTests
    integration_tests: IntegrationTests


# --- Logging Models ---
class LoggingValue(BaseModel):
    """Value object for logging details."""
    framework: Optional[str] = Field(description="The logging framework or facade, e.g., 'SLF4J with Logback'.")
    standard: Optional[str] = Field(description="The observed logging standard or format.")


class Logging(BaseModel):
    """Contains all details about the project's logging implementation."""
    category: str = Field(description="Category for logging analysis.", default="logging")
    value: LoggingValue


# --- Main Pydantic Class ---
class RepositoryAnalysis(BaseModel):
    """The root model for a complete technical analysis of a Git repository."""
    language: CategoryWithValue = Field(description="The primary programming language of the repository.")
    framework: CategoryWithValue = Field(description="The main framework used in the repository.")
    build_tool: CategoryWithValue = Field(description="The build automation tool used.")
    code_style: CodeStyle = Field(description="Analysis of coding standards and structure.")
    testing: Testing = Field(description="Analysis of testing frameworks and practices.")
    logging: Logging = Field(description="Analysis of the logging framework and standards.")


if __name__ == '__main__':
    # Example usage:
    json_data = {
        "language": {
            "category": "language",
            "value": {
                "name": "Java",
                "version": "17"
            }
        },
        "framework": {
            "category": "framework",
            "value": {
                "name": "Spring Boot",
                "version": "3.2.0"
            }
        },
        "build_tool": {
            "category": "build_tool",
            "value": {
                "name": "Gradle",
                "version": None
            }
        },
        "code_style": {
            "naming_conventions": {
                "category": "naming",
                "value": "Java standard conventions (PascalCase for classes, camelCase for methods/variables)"
            },
            "package_structure": {
                "category": "package_structure",
                "value": "Layer-based (e.g., 'controller' package for web layer)"
            }
        },
        "testing": {
            "unit_tests": {
                "category": "testing",
                "value": {
                    "framework": "JUnit 5",
                    "coverage": None
                }
            },
            "integration_tests": {
                "category": "testing",
                "value": {
                    "framework": "Spring Boot Test with JUnit 5",
                    "path": "src/test/java/com/canonical/controller/HealthControllerTest.java"
                }
            }
        },
        "logging": {
            "category": "logging",
            "value": {
                "framework": "SLF4J with Logback (Spring Boot default)",
                "standard": None
            }
        }
    }

    # Pydantic will parse and validate the JSON data against the model
    try:
        analysis_result = RepositoryAnalysis.model_validate(json_data)

        # You now have a strongly-typed Python object
        print("Successfully validated JSON data.")
        print(f"Language: {analysis_result.language.value.name}")
        print(f"Framework: {analysis_result.framework.value.name}")

        # You can easily convert the Pydantic model back to a JSON string
        print("\n--- Output as JSON ---")
        print(analysis_result.model_dump_json(indent=2))

    except Exception as e:
        print(f"Validation failed: {e}")