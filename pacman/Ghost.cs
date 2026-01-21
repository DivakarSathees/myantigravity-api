using System;

namespace PacMan
{
    public class Ghost
    {
        public int X { get; private set; }
        public int Y { get; private set; }

        private Random rnd = new Random();
        private bool moveToggle = false; // toggles movement to halve speed

        public Ghost(int startX, int startY)
        {
            X = startX;
            Y = startY;
        }

        public void Update(Map map, Player player)
        {
            // reduce ghost movement by 50%: only move on every other update call
            moveToggle = !moveToggle;
            if (!moveToggle) return;

            // simple chase: try to move closer on x or y randomly
            int dx = Math.Sign(player.X - X);
            int dy = Math.Sign(player.Y - Y);

            if (rnd.Next(2) == 0)
            {
                if (!map.IsWall(X + dx, Y)) X += dx;
                else if (!map.IsWall(X, Y + dy)) Y += dy;
            }
            else
            {
                if (!map.IsWall(X, Y + dy)) Y += dy;
                else if (!map.IsWall(X + dx, Y)) X += dx;
            }
        }
    }
}
