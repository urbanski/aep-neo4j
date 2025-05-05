#!/usr/bin/env python3
import json
import csv
import os

# Load the JSON data
with open('aep/data/agent_promises.json', 'r') as f:
    data = json.load(f)

# Create output directory if it doesn't exist
output_dir = 'neo4j_import'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 1. Export techniques (nodes)
with open(f'{output_dir}/techniques.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['techniqueId:ID', 'name', 'agent_class:string[]'])
    
    for technique_id, technique_data in data.items():
        agent_class = technique_data.get('agent_class', [])
        agent_class_str = ';'.join(agent_class) if agent_class else ''  # Neo4j format for arrays
        writer.writerow([
            technique_id,
            technique_data.get('name', ''),
            agent_class_str
        ])

# 2. Export provides relationships
with open(f'{output_dir}/provides_relationships.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([':START_ID', ':END_ID', ':TYPE'])
    
    for technique_id, technique_data in data.items():
        provides = technique_data.get('provides', [])
        for capability in provides:
            writer.writerow([technique_id, capability, 'PROVIDES'])

# 3. Export requires relationships
with open(f'{output_dir}/requires_relationships.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([':START_ID', ':END_ID', ':TYPE'])
    
    for technique_id, technique_data in data.items():
        requires = technique_data.get('requires', [])
        if requires:
            for requirement in requires:
                writer.writerow([technique_id, requirement, 'REQUIRES'])

# 4. Export mitigations
with open(f'{output_dir}/mitigations.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['mitigationId:ID', 'name'])
    
    # Gather all unique mitigations
    all_mitigations = set()
    for technique_data in data.values():
        mitigations = technique_data.get('mitigations', [])
        for mitigation in mitigations:
            all_mitigations.add(mitigation)
    
    # Write each unique mitigation
    for mitigation in all_mitigations:
        mitigation_id = mitigation.split(']')[0].strip('[') if '[' in mitigation else mitigation
        name = mitigation.split(']')[1].strip() if ']' in mitigation else mitigation
        writer.writerow([mitigation_id, name])

# 5. Export mitigation relationships
with open(f'{output_dir}/mitigation_relationships.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([':START_ID', ':END_ID', ':TYPE'])
    
    for technique_id, technique_data in data.items():
        mitigations = technique_data.get('mitigations', [])
        for mitigation in mitigations:
            mitigation_id = mitigation.split(']')[0].strip('[') if '[' in mitigation else mitigation
            writer.writerow([mitigation_id, technique_id, 'MITIGATES'])

# 6. Export capabilities (tactical goals)
with open(f'{output_dir}/capabilities.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['capabilityId:ID', 'name'])
    
    # Gather all unique capabilities
    all_capabilities = set()
    for technique_data in data.values():
        capabilities = technique_data.get('provides', [])
        for capability in capabilities:
            all_capabilities.add(capability)
        
        # Also check conditional_provides
        conditional = technique_data.get('conditional_provides', {})
        for condition_capabilities in conditional.values():
            for capability in condition_capabilities:
                all_capabilities.add(capability)
    
    # Write each unique capability
    for capability in all_capabilities:
        writer.writerow([capability, capability.replace('_', ' ').title()])

# 7. Export conditional provides
with open(f'{output_dir}/conditional_provides.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([':START_ID', ':END_ID', ':TYPE', 'condition'])
    
    for technique_id, technique_data in data.items():
        conditional = technique_data.get('conditional_provides', {})
        for condition, capabilities in conditional.items():
            for capability in capabilities:
                writer.writerow([technique_id, capability, 'CONDITIONALLY_PROVIDES', condition])

# 8. Export relevant_for relationships
with open(f'{output_dir}/relevant_for.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([':START_ID', 'systemType', ':TYPE'])
    
    for technique_id, technique_data in data.items():
        relevant_systems = technique_data.get('relevant_for', [])
        for system in relevant_systems:
            writer.writerow([technique_id, system, 'RELEVANT_FOR'])

# 9. Export child relationships
with open(f'{output_dir}/child_relationships.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([':START_ID', ':END_ID', ':TYPE'])
    
    for technique_id, technique_data in data.items():
        children = technique_data.get('children', [])
        for child in children:
            writer.writerow([technique_id, child, 'HAS_SUBTECHNIQUE'])

print(f"CSV files created in {output_dir}/ directory")
print("Files created:")
print("  - techniques.csv: All ATT&CK techniques")
print("  - capabilities.csv: Tactical goals techniques can provide")
print("  - mitigations.csv: Mitigations for techniques")
print("  - provides_relationships.csv: What capabilities techniques provide")
print("  - requires_relationships.csv: What capabilities techniques require")
print("  - mitigation_relationships.csv: Which techniques mitigations address")
print("  - conditional_provides.csv: Conditional capabilities techniques can provide")
print("  - relevant_for.csv: System types techniques are relevant for")
print("  - child_relationships.csv: Subtechnique relationships")
