import unittest
from unittest.mock import patch, mock_open
import json
import random
from .faction_generator import generate_policy, politic_diff, generate_faction
from .faction_generator import main

class TestFactionGenerator(unittest.TestCase):

    def test_generate_policy(self):
        policy = generate_policy()
        self.assertEqual(len(policy), 10)
        for key, value in policy.items():
            self.assertIn(value[0], ["Communist", "Socialist", "Indifferent", "Capitalist", "Free-Capitalist",
                                     "Authoritarian", "Statist", "Libertarian", "Anarchist",
                                     "Traditionalist", "Conservative", "Progressive", "Accelerationist",
                                     "Globalist", "Diplomatic", "Patriotic", "Nationalist",
                                     "Militarist", "Strategic", "Pacifist",
                                     "Homogenous", "Preservationist", "Heterogeneous", "Multiculturalist",
                                     "Apostate", "Secularist", "Religious", "Devout",
                                     "Retributionist", "Punitive", "Correctivist", "Rehabilitative",
                                     "Ecologist", "Naturalist", "Productivist", "Industrialist",
                                     "Democratic", "Republican", "Oligarchic", "Autocratic"])
            self.assertIsInstance(value[1], float)

    ''' todo AE: fix this test -> "module 'faction_generator' not found" 
    @patch('faction_generator.random.choice')
    @patch('faction_generator.random.random')
    def test_generate_faction(self, mock_random, mock_choice):
        return #todo AE: fix this test -> "module 'faction_generator' not found"
        
        mock_choice.side_effect = ['Entity', 'Noun1', 'Noun2', 'Suffix']
        mock_random.side_effect = [0.7, 0.05, 0.5]

        orgtype, acronym, name, policy = generate_faction()
        self.assertEqual(orgtype, 'Entity')
        self.assertEqual(acronym, 'N')
        self.assertEqual(name, 'Noun1 Suffix')
        self.assertEqual(len(policy), 10)
    '''

if __name__ == '__main__':
    unittest.main()