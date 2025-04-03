import json
import pygame


class Records:
    def __init__(self):
        self.scores = []
        self.load_scores()

    def load_scores(self):
        try:
            with open('records.json', 'r') as f:
                self.scores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.scores = [200, 150, 100]

    def save_scores(self):
        with open('records.json', 'w') as f:
            json.dump(sorted(self.scores, reverse=True)[:3], f)

    def add_score(self, new_score):
        updated = False
        for i in range(len(self.scores)):
            if new_score > self.scores[i]:
                self.scores.insert(i, new_score)
                updated = True
                break
        if not updated and len(self.scores) < 3:
            self.scores.append(new_score)
        self.scores = sorted(self.scores, reverse=True)[:3]
        self.save_scores()
        return updated

    def draw_records(self, surface):
        font = pygame.font.Font(None, 48)
        text = font.render("Top Scores:", True, (255, 255, 255))
        surface.blit(text, (300, 200))

        y = 250
        for i, score in enumerate(self.scores):
            text = font.render(f"{i + 1}. {score}", True, (255, 215, 0) if i == 0 else
            (192, 192, 192) if i == 1 else
            (205, 127, 50))
            surface.blit(text, (320, y))
            y += 50