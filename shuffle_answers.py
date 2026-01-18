#!/usr/bin/env python3
"""
Script pour mélanger aléatoirement la position des bonnes réponses dans le QCM.
Garantit qu'il n'y a jamais plus de 2 réponses identiques consécutives.
"""

import re
import random

def shuffle_with_constraint(options_with_idx, previous_answers, max_consecutive=2):
    """
    Mélange les options en évitant d'avoir plus de max_consecutive
    réponses identiques consécutives.
    """
    max_attempts = 100

    for _ in range(max_attempts):
        shuffled = options_with_idx.copy()
        random.shuffle(shuffled)

        # Trouver le nouvel index de la bonne réponse
        new_correct_idx = next(j for j, (orig_idx, _) in enumerate(shuffled) if orig_idx == 0)

        # Vérifier la contrainte avec les réponses précédentes
        recent = previous_answers[-(max_consecutive):] if len(previous_answers) >= max_consecutive else previous_answers

        if len(recent) < max_consecutive or not all(ans == new_correct_idx for ans in recent):
            return shuffled, new_correct_idx

    # Fallback: retourner quand même un résultat
    return shuffled, new_correct_idx

def shuffle_answers(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    result_lines = []

    i = 0
    questions_modified = 0
    all_correct_answers = []  # Pour suivre toutes les bonnes réponses

    while i < len(lines):
        line = lines[i]

        # Détecter le début d'une question
        if 'question:' in line and '"' in line:
            question_block = [line]
            i += 1

            options = []
            correct_idx = None
            in_options = False

            while i < len(lines):
                current_line = lines[i]
                question_block.append(current_line)

                if 'options:' in current_line and '[' in current_line:
                    in_options = True
                elif in_options:
                    stripped = current_line.strip()
                    if stripped.startswith('"'):
                        clean_option = stripped.rstrip(',')
                        options.append(clean_option)
                    if '],\n' in current_line or current_line.strip() == '],':
                        in_options = False

                if 'correct:' in current_line:
                    correct_match = re.search(r'correct:\s*(\d+)', current_line)
                    if correct_match:
                        correct_idx = int(correct_match.group(1))

                if 'explanation:' in current_line:
                    break

                i += 1

            if len(options) == 4 and correct_idx is not None:
                # Réorganiser pour que la bonne réponse soit à l'index 0 temporairement
                correct_option = options[correct_idx]
                other_options = [opt for idx, opt in enumerate(options) if idx != correct_idx]

                # Créer la liste avec la bonne réponse à l'index 0
                options_with_idx = [(0, correct_option)] + [(i+1, opt) for i, opt in enumerate(other_options)]

                # Mélanger avec contrainte
                shuffled_options, new_correct_idx = shuffle_with_constraint(
                    options_with_idx,
                    all_correct_answers,
                    max_consecutive=2
                )

                all_correct_answers.append(new_correct_idx)

                # Reconstruire le bloc
                new_block = []
                option_counter = 0
                in_options_rebuild = False

                for block_line in question_block:
                    if 'options:' in block_line and '[' in block_line:
                        in_options_rebuild = True
                        new_block.append(block_line)
                    elif in_options_rebuild and block_line.strip().startswith('"'):
                        _, shuffled_option = shuffled_options[option_counter]
                        indent = len(block_line) - len(block_line.lstrip())
                        indent_str = ' ' * indent
                        if option_counter < 3:
                            new_block.append(f'{indent_str}{shuffled_option},')
                        else:
                            new_block.append(f'{indent_str}{shuffled_option}')
                        option_counter += 1
                        if option_counter >= 4:
                            in_options_rebuild = False
                    elif 'correct:' in block_line:
                        new_line = re.sub(r'correct:\s*\d+', f'correct: {new_correct_idx}', block_line)
                        new_block.append(new_line)
                    else:
                        new_block.append(block_line)

                result_lines.extend(new_block)
                questions_modified += 1
            else:
                result_lines.extend(question_block)
        else:
            result_lines.append(line)

        i += 1

    # Afficher les statistiques
    print(f"Questions modifiées: {questions_modified}")

    # Distribution des réponses
    from collections import Counter
    dist = Counter(all_correct_answers)
    print(f"Distribution: A={dist[0]}, B={dist[1]}, C={dist[2]}, D={dist[3]}")

    # Vérifier les séries consécutives
    max_streak = 1
    current_streak = 1
    for i in range(1, len(all_correct_answers)):
        if all_correct_answers[i] == all_correct_answers[i-1]:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    print(f"Plus longue série consécutive: {max_streak}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result_lines))

if __name__ == '__main__':
    random.seed()  # Utiliser une graine vraiment aléatoire
    shuffle_answers('index.html', 'index.html')
    print("Terminé!")
