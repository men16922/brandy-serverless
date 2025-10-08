#!/usr/bin/env python3
"""
Data Schema Validation Script
Validates JSON data files for Product Insight Agent
"""

import sys
import os
import json

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda', 'agents', 'product-insight'))

def main():
    """Validate all data JSON files"""
    
    print("=" * 80)
    print("PRODUCT INSIGHT AGENT - DATA SCHEMA VALIDATION")
    print("=" * 80)
    
    try:
        from data_schema import (
            DataSchemaValidator,
            load_industry_data,
            load_region_data,
            load_size_data
        )
        
        print("\n✓ Successfully imported data_schema module")
        
        # Define file paths
        data_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'src',
            'lambda',
            'agents',
            'product-insight',
            'data'
        )
        
        industry_file = os.path.join(data_dir, 'industry_data.json')
        region_file = os.path.join(data_dir, 'region_data.json')
        size_file = os.path.join(data_dir, 'size_data.json')
        
        # Check if files exist
        print("\n" + "-" * 80)
        print("Checking Data Files")
        print("-" * 80)
        
        files_exist = True
        for file_path, name in [
            (industry_file, "industry_data.json"),
            (region_file, "region_data.json"),
            (size_file, "size_data.json")
        ]:
            if os.path.exists(file_path):
                print(f"✓ {name} exists")
            else:
                print(f"✗ {name} NOT FOUND")
                files_exist = False
        
        if not files_exist:
            print("\n✗ Some data files are missing!")
            return 1
        
        # Load and validate each file
        print("\n" + "-" * 80)
        print("Validating Data Schemas")
        print("-" * 80)
        
        all_valid = True
        
        # Validate industry data
        print("\n1. Industry Data")
        try:
            industry_data = load_industry_data(industry_file)
            print(f"   ✓ Valid schema")
            print(f"   ✓ {len(industry_data)} industries loaded")
            print(f"   Industries: {', '.join(industry_data.keys())}")
        except Exception as e:
            print(f"   ✗ Validation failed: {str(e)}")
            all_valid = False
        
        # Validate region data
        print("\n2. Region Data")
        try:
            region_data = load_region_data(region_file)
            print(f"   ✓ Valid schema")
            print(f"   ✓ {len(region_data)} regions loaded")
            print(f"   Regions: {', '.join(region_data.keys())}")
        except Exception as e:
            print(f"   ✗ Validation failed: {str(e)}")
            all_valid = False
        
        # Validate size data
        print("\n3. Size Data")
        try:
            size_data = load_size_data(size_file)
            print(f"   ✓ Valid schema")
            print(f"   ✓ {len(size_data)} sizes loaded")
            print(f"   Sizes: {', '.join(size_data.keys())}")
        except Exception as e:
            print(f"   ✗ Validation failed: {str(e)}")
            all_valid = False
        
        # Validate all together
        if all_valid:
            print("\n" + "-" * 80)
            print("Cross-Validation")
            print("-" * 80)
            
            is_valid, errors = DataSchemaValidator.validate_all_data_files(
                industry_data,
                region_data,
                size_data
            )
            
            if is_valid:
                print("✓ All data files are valid and consistent")
            else:
                print("✗ Cross-validation found issues:")
                for data_type, error_list in errors.items():
                    print(f"\n{data_type.upper()} errors:")
                    for error in error_list:
                        print(f"  - {error}")
                all_valid = False
        
        # Summary
        print("\n" + "=" * 80)
        if all_valid:
            print("✓ ALL VALIDATIONS PASSED")
            print("=" * 80)
            print("\nData files are ready for use!")
            print("\nSchema Requirements:")
            print("  - Industry: 7 required fields, 3+ items in lists")
            print("  - Region: 8 required fields, 3+ items in lists")
            print("  - Size: 8 required fields, 3+ items in lists")
            print("\nAll JSON files maintain consistent structure ✓")
            return 0
        else:
            print("✗ VALIDATION FAILED")
            print("=" * 80)
            print("\nPlease fix the errors above and try again.")
            return 1
            
    except ImportError as e:
        print(f"\n✗ Import error: {str(e)}")
        print("  Make sure data_schema.py exists in the correct location")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
