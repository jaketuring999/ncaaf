#!/usr/bin/env python3
"""
Validate NCAAF system prompt structure against OpenAI best practices.
"""

import xml.etree.ElementTree as ET
import re

def validate_prompt_structure(filepath):
    """Validate prompt structure against best practices."""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    results = {
        'structure': check_structure(content),
        'reasoning_order': check_reasoning_order(content), 
        'examples': check_examples(content),
        'format_validation': check_format_validation(content),
        'constraints': check_constraints(content)
    }
    
    return results

def check_structure(content):
    """Check if prompt follows recommended structure hierarchy."""
    required_sections = [
        'role_and_objective',
        'response_format', 
        'output_validation',
        'examples',
        'operational_rules'
    ]
    
    found_sections = []
    for section in required_sections:
        if f'<{section}>' in content:
            found_sections.append(section)
    
    return {
        'required': required_sections,
        'found': found_sections,
        'missing': list(set(required_sections) - set(found_sections)),
        'score': len(found_sections) / len(required_sections)
    }

def check_reasoning_order(content):
    """Check if reasoning-before-conclusion is enforced."""
    reasoning_indicators = [
        'reasoning_order',
        'NEVER start with conclusions',
        'reasoning must come first',
        'Data Collection',
        'Edge Analysis', 
        'Recommendation'
    ]
    
    found = [indicator for indicator in reasoning_indicators if indicator in content]
    
    return {
        'indicators_found': found,
        'enforced': len(found) >= 4,
        'score': len(found) / len(reasoning_indicators)
    }

def check_examples(content):
    """Check if examples demonstrate exact desired behavior."""
    # Look for structured examples with input/output
    example_pattern = r'<input>.*?</input>.*?<output>.*?</output>'
    examples = re.findall(example_pattern, content, re.DOTALL)
    
    # Check for reasoning workflow in examples
    workflow_pattern = r'<reasoning_workflow>.*?</reasoning_workflow>'
    workflows = re.findall(workflow_pattern, content, re.DOTALL)
    
    return {
        'total_examples': len(examples),
        'with_workflows': len(workflows),
        'structured': len(examples) > 0,
        'demonstrates_process': len(workflows) > 0,
        'score': min(1.0, (len(examples) + len(workflows)) / 4)
    }

def check_format_validation(content):
    """Check if output format validation is present."""
    validation_indicators = [
        'pre_response_check',
        'verify',
        'regenerate',
        'validation',
        'missing',
        'checklist'
    ]
    
    found = [indicator for indicator in validation_indicators if indicator in content]
    
    return {
        'indicators_found': found,
        'has_validation': 'pre_response_check' in content,
        'score': len(found) / len(validation_indicators)
    }

def check_constraints(content):
    """Check if explicit constraints are defined."""
    constraint_indicators = [
        'character_limits',
        'maximum',
        'limit',
        'lines total',
        'characters',
        'tool calls'
    ]
    
    found = [indicator for indicator in constraint_indicators if indicator in content]
    
    return {
        'indicators_found': found,
        'has_limits': any('limit' in indicator for indicator in found),
        'score': len(found) / len(constraint_indicators)
    }

def print_validation_report(results):
    """Print formatted validation report."""
    print("=== NCAAF Prompt Validation Report ===\n")
    
    total_score = sum(result.get('score', 0) for result in results.values()) / len(results)
    print(f"Overall Score: {total_score:.2%}\n")
    
    for category, result in results.items():
        print(f"## {category.replace('_', ' ').title()}")
        score = result.get('score', 0)
        print(f"Score: {score:.2%}")
        
        if 'missing' in result and result['missing']:
            print(f"Missing: {', '.join(result['missing'])}")
        
        if 'indicators_found' in result:
            print(f"Found: {len(result['indicators_found'])}/{len(result.get('required', []))} indicators")
            
        print()
    
    print("=== Recommendations ===")
    if total_score >= 0.8:
        print("✅ Prompt structure meets OpenAI best practices")
    elif total_score >= 0.6:
        print("⚠️  Prompt structure is good but has room for improvement")
    else:
        print("❌ Prompt structure needs significant improvements")

if __name__ == "__main__":
    v2_file = "/Users/Jake/PycharmProjects/ncaaf/middleware/prompts/ncaaf-systemprompt-v2.xml"
    v3_file = "/Users/Jake/PycharmProjects/ncaaf/middleware/prompts/ncaaf-systemprompt-v3.xml"
    
    print("Validating v2 prompt:")
    v2_results = validate_prompt_structure(v2_file)
    print_validation_report(v2_results)
    
    print("\n" + "="*50 + "\n")
    
    print("Validating v3 prompt:")
    v3_results = validate_prompt_structure(v3_file)
    print_validation_report(v3_results)