class Camera:

    def __init__(self, x, y, cw, ch, cx, cy):
        self.x = x
        self.y = y
        self.cw = cw
        self.ch = ch
        self.cx = cx
        self.cy = cy


def to_camera_coordinates(x, y, cw, ch, cx, cy):

    (x, y) = (x - cx, y - cy)

    if x < 0 or y < 0 or x >= cw or y >= ch:
        return (None, None)

    return (x, y)
