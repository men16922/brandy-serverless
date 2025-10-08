"""
Data Schema Validator for Product Insight Agent
Ensures JSON data files maintain consistent structure
"""

from typing import Dict, Any, List, Optional
import json


class DataSchemaValidator:
    """Validates JSON data files against expected schemas"""
    
    # Required fields for each data type
    INDUSTRY_SCHEMA = {
        "required_fields": [
            "characteristics",
            "success_factors",
            "market_trends",
            "risk_factors",
            "base_score",
            "growth_potential",
            "competition_level"
        ],
        "field_types": {
            "characteristics": list,
            "success_factors": list,
            "market_trends": list,
            "risk_factors": list,
            "base_score": (int, float),
            "growth_potential": str,
            "competition_level": str
        },
        "list_min_length": {
            "characteristics": 3,
            "success_factors": 3,
            "market_trends": 3,
            "risk_factors": 3
        },
        "valid_values": {
            "growth_potential": ["LOW", "MEDIUM", "HIGH"],
            "competition_level": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH", "LOW_MEDIUM", "MEDIUM_HIGH"]
        }
    }
    
    REGION_SCHEMA = {
        "required_fields": [
            "market_size",
            "competition_level",
            "consumer_power",
            "rent_cost",
            "characteristics",
            "advantages",
            "challenges",
            "score_modifier"
        ],
        "field_types": {
            "market_size": str,
            "competition_level": str,
            "consumer_power": str,
            "rent_cost": str,
            "characteristics": list,
            "advantages": list,
            "challenges": list,
            "score_modifier": (int, float)
        },
        "list_min_length": {
            "characteristics": 3,
            "advantages": 3,
            "challenges": 3
        },
        "valid_values": {
            "market_size": ["SMALL", "MEDIUM", "LARGE", "VERY_LARGE", "SMALL_MEDIUM", "MEDIUM_LARGE"],
            "competition_level": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH", "LOW_MEDIUM", "MEDIUM_HIGH"],
            "consumer_power": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH", "LOW_MEDIUM", "MEDIUM_HIGH"],
            "rent_cost": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH", "LOW_MEDIUM", "MEDIUM_HIGH"]
        }
    }
    
    SIZE_SCHEMA = {
        "required_fields": [
            "characteristics",
            "advantages",
            "challenges",
            "strategies",
            "investment_range",
            "employee_range",
            "score_modifier",
            "risk_level"
        ],
        "field_types": {
            "characteristics": list,
            "advantages": list,
            "challenges": list,
            "strategies": list,
            "investment_range": str,
            "employee_range": str,
            "score_modifier": (int, float),
            "risk_level": str
        },
        "list_min_length": {
            "characteristics": 3,
            "advantages": 3,
            "challenges": 3,
            "strategies": 3
        },
        "valid_values": {
            "risk_level": ["LOW", "MEDIUM", "HIGH", "LOW_MEDIUM", "MEDIUM_HIGH"]
        }
    }
    
    @classmethod
    def validate_industry_data(cls, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate industry data JSON structure.
        
        Args:
            data: Industry data dictionary
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return cls._validate_data(data, cls.INDUSTRY_SCHEMA, "industry")
    
    @classmethod
    def validate_region_data(cls, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate region data JSON structure.
        
        Args:
            data: Region data dictionary
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return cls._validate_data(data, cls.REGION_SCHEMA, "region")
    
    @classmethod
    def validate_size_data(cls, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate size data JSON structure.
        
        Args:
            data: Size data dictionary
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return cls._validate_data(data, cls.SIZE_SCHEMA, "size")
    
    @classmethod
    def _validate_data(
        cls,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        data_type: str
    ) -> tuple[bool, List[str]]:
        """
        Validate data against schema.
        
        Args:
            data: Data dictionary to validate
            schema: Schema definition
            data_type: Type of data (for error messages)
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not isinstance(data, dict):
            return False, [f"{data_type} data must be a dictionary"]
        
        # Validate each entry
        for key, entry in data.items():
            if not isinstance(entry, dict):
                errors.append(f"{data_type}.{key}: Entry must be a dictionary")
                continue
            
            # Check required fields
            for field in schema["required_fields"]:
                if field not in entry:
                    errors.append(f"{data_type}.{key}: Missing required field '{field}'")
            
            # Check field types
            for field, expected_type in schema["field_types"].items():
                if field in entry:
                    if not isinstance(entry[field], expected_type):
                        errors.append(
                            f"{data_type}.{key}.{field}: "
                            f"Expected type {expected_type}, got {type(entry[field])}"
                        )
            
            # Check list minimum lengths
            if "list_min_length" in schema:
                for field, min_length in schema["list_min_length"].items():
                    if field in entry and isinstance(entry[field], list):
                        if len(entry[field]) < min_length:
                            errors.append(
                                f"{data_type}.{key}.{field}: "
                                f"List must have at least {min_length} items, got {len(entry[field])}"
                            )
            
            # Check valid values
            if "valid_values" in schema:
                for field, valid_values in schema["valid_values"].items():
                    if field in entry:
                        value = entry[field]
                        if value not in valid_values:
                            errors.append(
                                f"{data_type}.{key}.{field}: "
                                f"Invalid value '{value}'. Must be one of {valid_values}"
                            )
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @classmethod
    def validate_all_data_files(
        cls,
        industry_data: Dict[str, Any],
        region_data: Dict[str, Any],
        size_data: Dict[str, Any]
    ) -> tuple[bool, Dict[str, List[str]]]:
        """
        Validate all data files at once.
        
        Args:
            industry_data: Industry data dictionary
            region_data: Region data dictionary
            size_data: Size data dictionary
        
        Returns:
            Tuple of (all_valid, errors_by_type)
        """
        all_errors = {}
        
        # Validate industry data
        is_valid, errors = cls.validate_industry_data(industry_data)
        if not is_valid:
            all_errors["industry"] = errors
        
        # Validate region data
        is_valid, errors = cls.validate_region_data(region_data)
        if not is_valid:
            all_errors["region"] = errors
        
        # Validate size data
        is_valid, errors = cls.validate_size_data(size_data)
        if not is_valid:
            all_errors["size"] = errors
        
        all_valid = len(all_errors) == 0
        return all_valid, all_errors


def load_and_validate_json(
    file_path: str,
    validator_func: callable,
    data_type: str
) -> Dict[str, Any]:
    """
    Load JSON file and validate its structure.
    
    Args:
        file_path: Path to JSON file
        validator_func: Validation function to use
        data_type: Type of data (for error messages)
    
    Returns:
        Validated data dictionary
    
    Raises:
        ValueError: If data is invalid
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is malformed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"{data_type} data file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {data_type} data file: {str(e)}",
            e.doc,
            e.pos
        )
    
    # Validate structure
    is_valid, errors = validator_func(data)
    
    if not is_valid:
        error_msg = f"{data_type} data validation failed:\n"
        error_msg += "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_msg)
    
    return data


# Convenience functions
def load_industry_data(file_path: str) -> Dict[str, Any]:
    """Load and validate industry data JSON"""
    return load_and_validate_json(
        file_path,
        DataSchemaValidator.validate_industry_data,
        "Industry"
    )


def load_region_data(file_path: str) -> Dict[str, Any]:
    """Load and validate region data JSON"""
    return load_and_validate_json(
        file_path,
        DataSchemaValidator.validate_region_data,
        "Region"
    )


def load_size_data(file_path: str) -> Dict[str, Any]:
    """Load and validate size data JSON"""
    return load_and_validate_json(
        file_path,
        DataSchemaValidator.validate_size_data,
        "Size"
    )
