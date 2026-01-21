using System;

namespace PacMan
{
    public class Player
    {
        public int X { get; private set; }
        public int Y { get; private set; }
        private int dirX = 0;
        private int dirY = 0;

        public Player(int startX, int startY)
        {
            X = startX;
            Y = startY;
        }

        public void SetDirection(int dx, int dy)
        {
            dirX = dx;
            dirY = dy;
        }

        public void Update(Map map)
        {
            var newX = X + dirX;
            var newY = Y + dirY;
            if (!map.IsWall(newX, newY))
            {
                X = newX;
                Y = newY;
                map.TryConsumePellet(X, Y);
            }
        }
    }
}
