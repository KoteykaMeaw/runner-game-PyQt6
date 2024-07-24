import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtGui import QPainter, QBrush, QColor, QPixmap
from PyQt6.QtCore import QUrl, QRect, Qt, QTimer, pyqtSignal
import random
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QSoundEffect
class GameObject:
    def __init__(self, x, y, width, height, color, image,damage):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.image = image
        self.damage = damage

    def draw(self, painter):
        painter.setBrush(QBrush(QColor(*self.color)))
        painter.drawRect(QRect(self.x, self.y, self.width, self.height))

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def drawImage(self, painter):
        painter.drawPixmap(self.x, self.y, self.image)

class Obstacle(GameObject):
    def __init__(self, x, y, width, height, color,image,damage):
        super().__init__(x, y, width, height, color,image,damage)

class Player(GameObject):
    def __init__(self, x, y, width, height, color, image,damage):
        super().__init__(x, y, width, height, color, image,damage)
        self.is_crouching = False
        self.is_jumping = False
        self.jump_velocity = 15
        self.speed = 1
        self.groundY = 250
        self.jumpSnd = "jump.mp3"
        self.damageSnd = "damage.mp3"
        self.MusicBackground = "background.mp3"
        self.IFramed = False
        self.iFrameTimer = QTimer()
        self.iFrameTimer.timeout.connect(self.endIFrame)
        self.Health = 100
        self.normalImage = QPixmap("plrNew.png")
        self.crouchImage = QPixmap("ohgod.png")
        self.image = image

        self.AudioPlayer = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.AudioPlayer.setAudioOutput(self.audio_output)

        self.background_music = QMediaPlayer()
        self.background_music_output = QAudioOutput()
        self.background_music.setAudioOutput(self.background_music_output)

        self.crouchOffset = self.normalImage.height() - self.crouchImage.height()

        self.background_music.setSource(QUrl.fromLocalFile(self.MusicBackground))
        self.background_music_output.setVolume(0.2)
        self.background_music.play()

    def jump(self):
        if not self.is_jumping and not self.is_crouching:
            self.is_jumping = True
            self.AudioPlayer.setSource(QUrl.fromLocalFile(self.jumpSnd))
            self.AudioPlayer.play()


    def crouch(self):
        if not self.is_jumping and not self.is_crouching:
            self.is_crouching = True
            self.image = self.crouchImage
            self.height = self.crouchImage.height()

    def uncrouch(self):
        if self.is_crouching:
            self.is_crouching = False
            self.image = self.normalImage
            self.height = self.normalImage.height()

    def update(self):
        if self.is_jumping and not self.is_crouching:
            self.y -= self.jump_velocity
            self.jump_velocity -= 1
            if self.y >= self.groundY:
                self.y = self.groundY
                self.is_jumping = False
                self.jump_velocity = 15


    def drawPlr(self, painter):
        if self.is_crouching:
            painter.drawPixmap(self.x, self.y + self.crouchOffset, self.image)
        else:
            painter.drawPixmap(self.x, self.y, self.image)
    def startIFrame(self):
        self.IFramed = True
        self.iFrameTimer.start(1000)

    def endIFrame(self):
        self.IFramed = False
        self.iFrameTimer.stop()

class RunnerGame(QWidget):
    gameOverSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Runner Game")
        self.setGeometry(100, 100, 600, 400)
        self.setFixedSize(600, 400)

        self.player = Player(50, 250, 20, 40, (0, 255, 0), QPixmap("plrNew.png"),0)
        self.obstacles = []
        self.obstacleSpeed = 5
        self.game_over = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.updater)
        self.timer.start(1000 // 60)


        self.spawnObstacleTimer = QTimer()
        self.spawnObstacleTimer.timeout.connect(self.spawnObstacle)
        self.spawnObstacleTimer.start(1500)

        self.groundWidth = 600
        self.groundHeight = 100
        self.groundX = 0

        self.score = 0
        self.previous_score = 0
        self.score_label = QLabel(f"Score: {self.score}", self)
        self.score_label.setGeometry(10, 10, 100, 20)

        self.hp_label = QLabel(f"Health: {self.player.Health}", self)
        self.hp_label.setGeometry(10, 30, 100, 20)

        self.game_over_screen = QWidget(self)
        self.game_over_screen.setGeometry(self.rect())
        self.game_over_screen.hide()
        self.game_over_label = QLabel("Game Over!", self.game_over_screen)
        self.game_over_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.try_again_button = QPushButton("Try Again", self.game_over_screen)
        self.try_again_button.clicked.connect(self.restart_game)
        layout = QVBoxLayout()
        layout.addWidget(self.game_over_label)
        layout.addWidget(self.try_again_button)
        self.game_over_screen.setLayout(layout)
        self.gameOverSignal.connect(self.show_game_over_screen)

        self.player_rect = QRect(self.player.x, self.player.y, self.player.image.width(), self.player.image.height())

        self.obstacleImage1 = QPixmap("spikeObstacle.png")
        self.obstacleImage2 = QPixmap("chainsaw.png")

        self.skyIMG = QPixmap("sky.png")
        self.groundIMG = QPixmap("grassNew.png")




    def paintEvent(self, event):
        if not self.game_over:
            painter = QPainter(self)

            painter.drawPixmap(0, 0, self.skyIMG)
            painter.drawPixmap(0, -75, self.groundIMG)


            self.player.drawPlr(painter)

            for obstacle in self.obstacles:
                obstacle.drawImage(painter)

    def updater(self):
        if self.game_over != True:
            self.player.update()

            if self.player.is_crouching:
                player_height = self.player.crouchImage.height()
            else:
                player_height = self.player.image.height()

            self.player_rect.setRect(self.player.x, self.player.y, self.player.image.width(), player_height)

            print("Width: ",self.player.image.width(), "Height: " , player_height)

            for obstacle in self.obstacles:
                obstacle.move(-self.obstacleSpeed, 0)

            self.obstacles = [obstacle for obstacle in self.obstacles if obstacle.x + obstacle.width > 0]

            self.check_collisions()

            if self.player.x < 0:
                self.player.x = 0
            if self.player.x > 600:
                self.player.x = 0

            self.score += 1

            if self.score != self.previous_score:
                self.score_label.setText(f"Score: {self.score}")

                self.previous_score = self.score

            self.update()

    def check_collisions(self):
        if self.player.is_crouching:
            player_height = self.player.crouchImage.height()
        else:
            player_height = self.player.height
        self.player_rect.setRect(self.player.x, self.player.y, self.player.image.width(), player_height)

        for obstacle in self.obstacles:
            obstacle_rect = QRect(obstacle.x, obstacle.y, obstacle.image.width(), obstacle.image.height())

            print("OBS Width: ", obstacle.image.width(), "OBS Height: ", obstacle.image.height())
            print("Collides: ", self.player_rect.intersects(obstacle_rect))

            if self.player_rect.intersects(obstacle_rect) and self.game_over != True and self.player.IFramed == False:
                self.player.AudioPlayer.setSource(QUrl.fromLocalFile(self.player.damageSnd))
                self.player.AudioPlayer.play()
                self.player.Health -= obstacle.damage
                self.player.startIFrame()

                if self.player.Health <= 0:
                    self.player.Health = 0
                    self.game_over = True
                    self.gameOverSignal.emit()

                self.hp_label.setText(f"Health: {self.player.Health}")
                break

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space or event.key() == Qt.Key.Key_W or event.key() == Qt.Key.Key_Up:
            self.player.jump()
        if event.key() == Qt.Key.Key_S or event.key() == Qt.Key.Key_Down:
            self.player.crouch()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_S or event.key() == Qt.Key.Key_Down:
            self.player.uncrouch()

    def spawnObstacle(self):
        damage = 5

        if self.score >= 1000:
            obstacleImage = random.choice([self.obstacleImage1, self.obstacleImage2])
        else:
            obstacleImage = self.obstacleImage1

        if obstacleImage == self.obstacleImage1:
            damage = 5
        else:
            damage = 10

        obstaclex = self.width()
        obstacley = 300 - self.obstacleImage1.height()
        if obstacleImage == self.obstacleImage2:
            obstacley = 260 - self.obstacleImage1.height()
        obstaclewidth = self.obstacleImage1.width()
        obstacleheight = self.obstacleImage1.height()


        spawnRate = 6000 - (self.score * 50)
        if spawnRate < 1000:
            spawnRate = 1000

        newObstacle = Obstacle(obstaclex, obstacley, obstaclewidth, obstacleheight,
                               (255, 255, 255), obstacleImage,damage)
        self.obstacles.append(newObstacle)

        self.spawnObstacleTimer.stop()
        self.spawnObstacleTimer.start(spawnRate)
        self.obstacleSpeed = random.randint(3, 10)

    def show_game_over_screen(self):
        self.player.background_music.stop()
        self.game_over_screen.show()

    def restart_game(self):
        if self.game_over == True:
            self.player.x = 50
            self.player.y = 250
            self.player.is_jumping = False
            self.player.jump_velocity = 15
            self.obstacles = []
            self.game_over = False
            self.groundX = 0
            self.score = 0
            self.player.Health = 100
            self.hp_label.setText(f"Health: {self.player.Health}")

            self.player.background_music.setSource(QUrl.fromLocalFile(self.player.MusicBackground))
            self.player.background_music.play()

            self.game_over_screen.hide()

            self.setFocus()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = RunnerGame()
    game.show()
    sys.exit(app.exec())
