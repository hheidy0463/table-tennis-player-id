import os
import pickle
import numpy as np
import cv2

def is_number(s):
    return isinstance(s, (int, float)) or (isinstance(s, str) and s.replace('.', '', 1).isdigit())

def check_format_1(score_tokens):
    """Checks if the tokens are in the format <name> <score1> <score2> <name> <score1> <score2>"""
    
    if len(score_tokens) != 6:
        return False

    return (
        not is_number(score_tokens[0]) and  
        is_number(score_tokens[1]) and      
        is_number(score_tokens[2]) and      
        not is_number(score_tokens[3]) and  
        is_number(score_tokens[4]) and      
        is_number(score_tokens[5])          
    )

def check_format_2(score_tokens):
    return len(score_tokens) == 6 and (
        not is_number(score_tokens[0]) and  
        is_number(score_tokens[1]) and      
        is_number(score_tokens[2]) and      
        is_number(score_tokens[3]) and  
        is_number(score_tokens[4]) and      
        not is_number(score_tokens[5])          
    )

def check_format_3(score_tokens):
    return len(score_tokens) == 6 and (
        is_number(score_tokens[0]) and  
        is_number(score_tokens[1]) and      
        not is_number(score_tokens[2]) and      
        not is_number(score_tokens[3]) and  
        is_number(score_tokens[4]) and      
        is_number(score_tokens[5])          
    )

def check_format_4(score_tokens):
    return len(score_tokens) == 7 and (
        not is_number(score_tokens[0]) and  
        not is_number(score_tokens[1]) and      
        is_number(score_tokens[2]) and      
        is_number(score_tokens[3]) and  
        not is_number(score_tokens[4]) and      
        is_number(score_tokens[5]) and 
        is_number(score_tokens[6]) 
    )
def check_format_5(score_tokens):
    return len(score_tokens) == 7 and (
        not is_number(score_tokens[0]) and  
        is_number(score_tokens[1]) and      
        is_number(score_tokens[2]) and      
        not is_number(score_tokens[3]) and  
        not is_number(score_tokens[4]) and      
        is_number(score_tokens[5]) and 
        is_number(score_tokens[6]) 
    )

def check_format_6(score_tokens):
    return len(score_tokens) == 7 and (
        not is_number(score_tokens[0]) and  
        is_number(score_tokens[1]) and      
        is_number(score_tokens[2]) and      
        not is_number(score_tokens[3]) and  
        is_number(score_tokens[4]) and      
        is_number(score_tokens[5]) and 
        not is_number(score_tokens[6]) 
    )

def check_format_7(score_tokens):
    return len(score_tokens) == 9 and (
        not is_number(score_tokens[0]) and  
        not is_number(score_tokens[1]) and      
        not is_number(score_tokens[2]) and      
        is_number(score_tokens[3]) and  
        is_number(score_tokens[4]) and      
        not is_number(score_tokens[5]) and 
        not is_number(score_tokens[6]) and 
        is_number(score_tokens[7]) and
        is_number(score_tokens[8]) 
    )

def check_format_8(score_tokens):
    return len(score_tokens) == 7 and (
        not is_number(score_tokens[0]) and  
        not is_number(score_tokens[1]) and      
        is_number(score_tokens[2]) and      
        is_number(score_tokens[3]) and  
        is_number(score_tokens[4]) and      
        is_number(score_tokens[5]) and 
        not is_number(score_tokens[6])
    )

def check_format_9(score_tokens):
    return len(score_tokens) == 6 and (
        is_number(score_tokens[0]) and  
        is_number(score_tokens[1]) and      
        not is_number(score_tokens[2]) and      
        is_number(score_tokens[3]) and  
        is_number(score_tokens[4]) and      
        not is_number(score_tokens[5])
    )

def check_format_10(score_tokens):
    return len(score_tokens) == 7 and (
        not is_number(score_tokens[1]) and      
        is_number(score_tokens[2]) and      
        is_number(score_tokens[3]) and  
        not is_number(score_tokens[4]) and      
        is_number(score_tokens[5]) and 
        is_number(score_tokens[6])
    )

def winner_of_round(p1_round, p2_round):
    """
    Determine if the round is 'won' by either player under typical table-tennis rules:
      - Must have 11 or more points,
      - Must be at least 2 points ahead.
    Return:
      1 if Player 1 wins the round,
      2 if Player 2 wins the round,
      None otherwise.
    """
    # If p1 >= 11 and leads by >=2, p1 wins
    if p1_round >= 11 and (p1_round - p2_round) >= 2:
        return 1
    # If p2 >= 11 and leads by >=2, p2 wins
    if p2_round >= 11 and (p2_round - p1_round) >= 2:
        return 2
    return None

def is_reset(score):
    """Checks if this scoreboard is a 'reset' (start of a new game)."""
    return score == (0, 0, 0, 0)

def is_valid_transition(prev_score, next_score):
    """
    Decide if it's a valid scoreboard transition from prev_score to next_score.
    
    For example, you might allow:
      1) The same score (no change).
      2) A 'reset' to (0, 0, 0, 0).
      3) Exactly one player's round score incremented by 1.
      4) A possible jump from something like (p1_series, 11, p2_series, x)
         to (p1_series+1, 0, p2_series, 0) for a new game, etc.
    
    You can adjust this logic based on your table‐tennis rules and data quirks.
    """
    if next_score == prev_score:
        return True
    
    # Always allow going to a reset
    if is_reset(next_score):
        return True
    
    # Example: If next_score is a "one‐point" increment from prev_score
    # This is simplistic: we only check that exactly one of p1_round or p2_round
    # went up by 1, with everything else staying the same. You can expand.
    p1s_a, p1r_a, p2s_a, p2r_a = prev_score
    p1s_b, p1r_b, p2s_b, p2r_b = next_score
    
    # same series, one round increments
    one_step_p1 = (
        (p1s_b == p1s_a) and
        (p1r_b == p1r_a + 1) and
        (p2s_b == p2s_a) and
        (p2r_b == p2r_a)
    )
    one_step_p2 = (
        (p1s_b == p1s_a) and
        (p1r_b == p1r_a) and
        (p2s_b == p2s_a) and
        (p2r_b == p2r_a + 1)
    )
    if one_step_p1 or one_step_p2:
        return True
    
    # Example: if a “game” might have ended, we might see the round scores reset
    # and one player’s “series” go up by 1. This is very approximate:
    new_game_p1 = (
        p1s_b == p1s_a + 1 and
        p1r_b == 0 and
        p2s_b == p2s_a and
        p2r_b == 0
    )
    new_game_p2 = (
        p1s_b == p1s_a and
        p1r_b == 0 and
        p2s_b == p2s_a + 1 and
        p2r_b == 0
    )
    if new_game_p1 or new_game_p2:
        return True
    
    return False

# Added
def raw_token_lists_from_data(all_data):
    """
    Given the list of (ok, idx, result) tuples, extract for each valid detection
    the flat list of OCR tokens.
    Returns a list of (frame_idx, [token1, token2, ...]).
    """
    token_lists = []
    replacements = {"O": "0"}

    for ok, idx, result in all_data:
        # skip bad frames
        if not ok or result is None or (isinstance(result, str) and "OPTIM" in result):
            continue

        det = result[0]
        if det is None:
            continue

        # extract the text tokens
        tokens = [r[1][0] for r in det]

        # apply your simple replacements & drop dots
        for i, t in enumerate(tokens):
            if t in replacements:
                tokens[i] = replacements[t]
            if "." in tokens[i]:
                tokens[i] = tokens[i].replace(".", "")

        token_lists.append((idx, tokens))

    return token_lists



def scores_from_raw_data(all_data):
    replacements = {
        "O": "0"
    }
    validation = []
    scores = []
    for ok, idx, result in all_data:
        if "OPTIM" in result:
            validation.append(2)
            continue
        if not ok:
            validation.append(0)
            continue

        result = result[0]
        if result == None:
            continue
        score_tokens = [r[1][0] for r in result] # discards the bounding box and confidence measure
        for i, token in enumerate(score_tokens):
            if token in replacements:
                score_tokens[i] = replacements[token]
            if "." in token:
                # print(token)
                pass
                score_tokens[i] = token.replace(".", "")

        if len(score_tokens) == 8:
            # use case: TOMOKAZU HARIMOTO 0 1 LIN SHIDONG 0 0 instead of TOMOKAZU/HARIMOTO 0 1 LIN/SHIDONG 0 0
            team_1 = score_tokens[0] + "/" + score_tokens[1]
            team_2 = score_tokens[4] + "/" + score_tokens[5]
            score_tokens = [team_1, score_tokens[2], score_tokens[3], team_2, score_tokens[6], score_tokens[7]]

        if check_format_1(score_tokens):
            validation.append(1)
            first_series_score = int(score_tokens[1])
            first_round_score = int(score_tokens[2])
            second_series_score = int(score_tokens[4])
            second_round_score = int(score_tokens[5])
        elif check_format_2(score_tokens):
            # print("Type 2", score_tokens)
            validation.append(1)
            first_series_score = int(score_tokens[1])
            first_round_score = int(score_tokens[2])
            second_series_score = int(score_tokens[3])
            second_round_score = int(score_tokens[4])
        elif check_format_3(score_tokens):
            # print("Type 3", score_tokens)
            validation.append(1)
            first_series_score = int(score_tokens[0])
            first_round_score = int(score_tokens[1])
            second_series_score = int(score_tokens[4])
            second_round_score = int(score_tokens[5])
        elif check_format_4(score_tokens):
            # print("Type 4", score_tokens)
            validation.append(1)
            first_series_score = int(score_tokens[2])
            first_round_score = int(score_tokens[3])
            second_series_score = int(score_tokens[5])
            second_round_score = int(score_tokens[6])
        elif check_format_5(score_tokens):
            # print("Type 5", score_tokens)
            validation.append(1)
            first_series_score = int(score_tokens[1])
            first_round_score = int(score_tokens[2])
            second_series_score = int(score_tokens[5])
            second_round_score = int(score_tokens[6])
        elif check_format_6(score_tokens):
            # print("Type 6", score_tokens)
            validation.append(1)
            first_series_score = int(score_tokens[1])
            first_round_score = int(score_tokens[2])
            second_series_score = int(score_tokens[4])
            second_round_score = int(score_tokens[5])
        elif check_format_7(score_tokens):
            # print("Type 7", score_tokens)
            validation.append(1)
            first_series_score = int(score_tokens[3])
            first_round_score = int(score_tokens[4])
            second_series_score = int(score_tokens[7])
            second_round_score = int(score_tokens[8])
        elif check_format_8(score_tokens):
            # print("Type 8", score_tokens)
            validation.append(1)
            first_series_score = int(score_tokens[2])
            first_round_score = int(score_tokens[3])
            second_series_score = int(score_tokens[4])
            second_round_score = int(score_tokens[5])
        elif check_format_9(score_tokens):
            # print("Type 9", score_tokens)
            validation.append(1)
            first_series_score = int(score_tokens[0])
            first_round_score = int(score_tokens[1])
            second_series_score = int(score_tokens[3])
            second_round_score = int(score_tokens[4])
        elif check_format_10(score_tokens):
            # print("Type 10", score_tokens)
            validation.append(1)
            first_series_score = int(score_tokens[2])
            first_round_score = int(score_tokens[3])
            second_series_score = int(score_tokens[5])
            second_round_score = int(score_tokens[6])
        else:
            # print(len(score_tokens), score_tokens)
            validation.append(-1)
            continue
        scores.append((idx, (first_series_score, first_round_score, second_series_score, second_round_score)))
    return scores

def changes_from_scores(scores):
    current_start_idx, current_score = scores[0]

    changes = []
    changes_bad = 0
    # print("START", current_score)
    for idx, score in scores:
        if any([score[i] != current_score[i] for i in range(4)]):
            if is_valid_transition(current_score, score):
                # a proper score increase
                # print("GOOD", idx, current_score, score)
                changes.append(((current_start_idx, idx), current_score, score))
                current_start_idx, current_score = idx, score
            else:
                pass
                # print("BAD", idx, current_score, score)
                # wait patiently until the correct next score shows up

    return changes

def is_strict_valid_transition(prev_score, next_score):
    """
    Decide if it's a valid scoreboard transition from prev_score to next_score.
    
    For example, you might allow:
      1) The same score (no change).
      2) A 'reset' to (0, 0, 0, 0).
      3) Exactly one player's round score incremented by 1.
      4) A possible jump from something like (p1_series, 11, p2_series, x)
         to (p1_series+1, 0, p2_series, 0) for a new game, etc.
    
    You can adjust this logic based on your table‐tennis rules and data quirks.
    """
    p1s_a, p1r_a, p2s_a, p2r_a = prev_score
    p1s_b, p1r_b, p2s_b, p2r_b = next_score

    if (p1s_a == 3 or p2s_a == 3) and is_reset(next_score):
        return True
    
    # Example: If next_score is a "one‐point" increment from prev_score
    # This is simplistic: we only check that exactly one of p1_round or p2_round
    # went up by 1, with everything else staying the same. You can expand.
    
    # same series, one round increments
    one_step_p1 = (
        (p1s_b == p1s_a) and
        (p1r_b == p1r_a + 1) and
        (p2s_b == p2s_a) and
        (p2r_b == p2r_a)
    )
    one_step_p2 = (
        (p1s_b == p1s_a) and
        (p1r_b == p1r_a) and
        (p2s_b == p2s_a) and
        (p2r_b == p2r_a + 1)
    )
    if one_step_p1 or one_step_p2:
        return True
    
    # Example: if a “game” might have ended, we might see the round scores reset
    # and one player’s “series” go up by 1. This is very approximate:
    new_game_p1 = (
        # p1s_a == 10 and
        p1s_b == p1s_a + 1 and
        p1r_b == 0 and
        p2s_b == p2s_a and
        p2r_b == 0
    )
    new_game_p2 = (
        p1s_b == p1s_a and
        p1r_b == 0 and
        # p2s_a == 10 and
        p2s_b == p2s_a + 1 and
        p2r_b == 0
    )
    if new_game_p1 or new_game_p2:
        return True
    
    return False
