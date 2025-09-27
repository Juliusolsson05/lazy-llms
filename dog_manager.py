"""
Lazy Dog Manager - Testing MCP Integration with Dog Management
This module demonstrates lazy evaluation patterns for dog management.
"""
from typing import Optional, List, Dict
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Dog:
    """Represents a dog with lazy-loaded attributes"""
    name: str
    breed: str
    age: int
    weight: float
    owner: str
    vaccination_records: Optional[List[Dict]] = None

    @property
    def breed_info(self) -> Dict:
        """Lazily fetch breed information from AKC database"""
        return self._fetch_breed_info()

    def _fetch_breed_info(self) -> Dict:
        """Mock function to simulate fetching breed data"""
        breed_data = {
            "Golden Retriever": {
                "size": "Large",
                "temperament": "Friendly, Intelligent, Devoted",
                "exercise_needs": "High",
                "grooming": "Moderate to High"
            },
            "Poodle": {
                "size": "Variable",
                "temperament": "Active, Proud, Very Smart",
                "exercise_needs": "High",
                "grooming": "High"
            },
            "Beagle": {
                "size": "Small to Medium",
                "temperament": "Friendly, Curious, Merry",
                "exercise_needs": "Moderate",
                "grooming": "Low"
            }
        }
        return breed_data.get(self.breed, {"info": "Unknown breed"})

    @property
    def vaccination_status(self) -> str:
        """Lazily evaluate vaccination status"""
        if not self.vaccination_records:
            return "No records available"

        latest = max(self.vaccination_records, key=lambda x: x['date'])
        days_since = (datetime.now() - datetime.fromisoformat(latest['date'])).days

        if days_since > 365:
            return "Overdue for vaccination"
        elif days_since > 300:
            return "Vaccination due soon"
        else:
            return "Up to date"


class LazyDogRegistry:
    """Registry for managing dogs with lazy loading patterns"""

    def __init__(self):
        self._dogs: Dict[str, Dog] = {}
        self._loaded = False

    @property
    def dogs(self) -> Dict[str, Dog]:
        """Lazy load all dogs when first accessed"""
        if not self._loaded:
            self._load_dogs()
            self._loaded = True
        return self._dogs

    def _load_dogs(self):
        """Simulate loading dogs from database"""
        # Mock data for testing
        self._dogs = {
            "buddy": Dog(
                name="Buddy",
                breed="Golden Retriever",
                age=3,
                weight=70.5,
                owner="John Smith",
                vaccination_records=[
                    {"vaccine": "Rabies", "date": "2024-06-15T00:00:00"},
                    {"vaccine": "DHPP", "date": "2024-06-15T00:00:00"}
                ]
            ),
            "max": Dog(
                name="Max",
                breed="Beagle",
                age=5,
                weight=25.0,
                owner="Jane Doe",
                vaccination_records=[
                    {"vaccine": "Rabies", "date": "2023-03-10T00:00:00"},
                    {"vaccine": "DHPP", "date": "2023-03-10T00:00:00"}
                ]
            )
        }

    def register_dog(self, dog: Dog) -> str:
        """Register a new dog in the system"""
        dog_id = dog.name.lower()
        self.dogs[dog_id] = dog
        return f"Dog {dog.name} registered successfully with ID: {dog_id}"

    def get_dog(self, dog_id: str) -> Optional[Dog]:
        """Retrieve a dog by ID"""
        return self.dogs.get(dog_id)

    @lru_cache(maxsize=32)
    def find_dogs_by_breed(self, breed: str) -> List[Dog]:
        """Find all dogs of a specific breed (cached)"""
        return [dog for dog in self.dogs.values() if dog.breed == breed]

    def get_vaccination_report(self) -> Dict[str, str]:
        """Generate vaccination status report for all dogs"""
        return {
            dog.name: dog.vaccination_status
            for dog in self.dogs.values()
        }


def main():
    """Demo the lazy dog management system"""
    registry = LazyDogRegistry()

    # Register a new dog
    new_dog = Dog(
        name="Luna",
        breed="Poodle",
        age=2,
        weight=45.0,
        owner="Alice Johnson"
    )
    print(registry.register_dog(new_dog))

    # Get dog info (triggers lazy loading)
    buddy = registry.get_dog("buddy")
    if buddy:
        print(f"\n{buddy.name}'s breed info (lazy loaded):")
        print(buddy.breed_info)
        print(f"Vaccination status: {buddy.vaccination_status}")

    # Find dogs by breed (cached result)
    beagles = registry.find_dogs_by_breed("Beagle")
    print(f"\nFound {len(beagles)} Beagle(s)")

    # Generate vaccination report
    print("\nVaccination Report:")
    for dog_name, status in registry.get_vaccination_report().items():
        print(f"  {dog_name}: {status}")


if __name__ == "__main__":
    main()
