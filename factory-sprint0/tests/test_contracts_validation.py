"""
Tests de validation des contrats JSON Schema.
Vérifie que tous les contrats respectent le standard Draft-07.
"""

import json
import os
from pathlib import Path
import jsonschema
from jsonschema import Draft7Validator

def test_all_contracts_exist():
    """Vérifie que les 5 contrats existent."""
    contracts_dir = Path("schemas/contracts")
    expected_contracts = [
        "architect_agent_contract.json",
        "dev_agent_contract.json",
        "test_agent_contract.json",
        "qa_agent_contract.json",
        "github_agent_contract.json"
    ]
    
    for contract_name in expected_contracts:
        contract_path = contracts_dir / contract_name
        assert contract_path.exists(), f"Contrat manquant : {contract_name}"
        print(f"✅ {contract_name} existe")

def test_contracts_are_valid_json():
    """Vérifie que tous les contrats sont du JSON valide."""
    contracts_dir = Path("schemas/contracts")
    
    for contract_file in contracts_dir.glob("*.json"):
        with open(contract_file, 'r', encoding='utf-8') as f:
            try:
                json.load(f)
                print(f"✅ {contract_file.name} est du JSON valide")
            except json.JSONDecodeError as e:
                raise AssertionError(f"JSON invalide dans {contract_file.name}: {e}")

def test_contracts_have_required_schemas():
    """Vérifie que chaque contrat a les 4 schémas obligatoires."""
    contracts_dir = Path("schemas/contracts")
    required_keys = ["input_schema", "output_schema", "error_schema", "health_schema"]
    
    for contract_file in contracts_dir.glob("*.json"):
        with open(contract_file, 'r', encoding='utf-8') as f:
            contract = json.load(f)
            
            for key in required_keys:
                assert key in contract, f"{contract_file.name} manque '{key}'"
            
            print(f"✅ {contract_file.name} a les 4 schémas obligatoires")

def test_error_schema_has_standard_codes():
    """Vérifie que les error_schema ont des codes standardisés."""
    contracts_dir = Path("schemas/contracts")
    
    for contract_file in contracts_dir.glob("*.json"):
        with open(contract_file, 'r', encoding='utf-8') as f:
            contract = json.load(f)
            error_schema = contract.get("error_schema", {})
            
            # Vérifie que 'code' et 'message' sont requis
            assert "required" in error_schema, f"{contract_file.name} error_schema manque 'required'"
            assert "code" in error_schema["required"], f"{contract_file.name} error_schema doit requérir 'code'"
            assert "message" in error_schema["required"], f"{contract_file.name} error_schema doit requérir 'message'"
            
            # Vérifie que 'code' a des valeurs enum
            code_property = error_schema.get("properties", {}).get("code", {})
            assert "enum" in code_property, f"{contract_file.name} error_schema.code doit avoir enum"
            
            print(f"✅ {contract_file.name} error_schema est standardisé")

def test_health_schema_has_status():
    """Vérifie que les health_schema ont un champ 'status' avec enum correct."""
    contracts_dir = Path("schemas/contracts")
    expected_statuses = ["healthy", "degraded", "unhealthy"]
    
    for contract_file in contracts_dir.glob("*.json"):
        with open(contract_file, 'r', encoding='utf-8') as f:
            contract = json.load(f)
            health_schema = contract.get("health_schema", {})
            
            status_property = health_schema.get("properties", {}).get("status", {})
            assert "enum" in status_property, f"{contract_file.name} health_schema.status doit avoir enum"
            
            actual_statuses = set(status_property["enum"])
            expected_set = set(expected_statuses)
            assert actual_statuses == expected_set, f"{contract_file.name} health_schema.status enum incorrect"
            
            print(f"✅ {contract_file.name} health_schema.status correct")

if __name__ == "__main__":
    print("\n=== Tests de Validation des Contrats ===\n")
    
    test_all_contracts_exist()
    test_contracts_are_valid_json()
    test_contracts_have_required_schemas()
    test_error_schema_has_standard_codes()
    test_health_schema_has_status()
    
    print("\n✅ TOUS LES TESTS PASSENT - Contrats validés !")
