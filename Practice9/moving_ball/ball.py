


class Ball:
    
    RADIUS  = 25          
    STEP    = 20         
    COLOR   = (220, 30, 30)

    def __init__(self, screen_width, screen_height):
        self.screen_w = screen_width
        self.screen_h = screen_height
        self.radius   = self.RADIUS
        self.step     = self.STEP
        self.color    = self.COLOR
        # Start in the centre
        self.x = screen_width  // 2
        self.y = screen_height // 2

   

    def move_up(self):
       
        new_y = self.y - self.step
        if new_y - self.radius >= 0:
            self.y = new_y

    def move_down(self):
        
        new_y = self.y + self.step
        if new_y + self.radius <= self.screen_h:
            self.y = new_y

    def move_left(self):
        
        new_x = self.x - self.step
        if new_x - self.radius >= 0:
            self.x = new_x

    def move_right(self):
        
        new_x = self.x + self.step
        if new_x + self.radius <= self.screen_w:
            self.x = new_x

   

    def get_pos(self):
        
        return (self.x, self.y)
