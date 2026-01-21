using System;
using System.Linq;

namespace PacMan
{
    public class Map
    {
        private string[] layout = new string[]
        {
            "####################",
            "#........#.........#",
            "#.##.###.#.###.##.#.#",
            "#..................#",
            "#.##.#.#####.#.##..#",
            "#....#...#...#.....#",
            "####################",
        };

        private char[,] grid;
        public int Width { get; }
        public int Height { get; }
        public int StartX { get; }
        public int StartY { get; }
        public int GhostX { get; }
        public int GhostY { get; }

        public int PelletCount { get; private set; }

        public Map()
        {
            Height = layout.Length;
            Width = layout[0].Length;
            grid = new char[Width, Height];

            for (int y = 0; y < Height; y++)
            {
                var row = layout[y];
                for (int x = 0; x < Width; x++)
                {
                    var c = row[x];
                    grid[x, y] = c;
                }
            }

            // find start (first dot) and ghost (first space near center)
            var firstDot = FindChar('.');
            StartX = firstDot.x;
            StartY = firstDot.y;

            var centerX = Width / 2;
            var centerY = Height / 2;
            GhostX = centerX;
            GhostY = centerY;

            PelletCount = CountPellets();
        }

        private (int x, int y) FindChar(char t)
        {
            for (int y = 0; y < Height; y++)
                for (int x = 0; x < Width; x++)
                    if (grid[x, y] == t)
                        return (x, y);
            return (1, 1);
        }

        private int CountPellets()
        {
            int c = 0;
            for (int y = 0; y < Height; y++)
                for (int x = 0; x < Width; x++)
                    if (grid[x, y] == '.') c++;
            return c;
        }

        public bool IsWall(int x, int y)
        {
            if (x < 0 || y < 0 || x >= Width || y >= Height) return true;
            return grid[x, y] == '#';
        }

        public bool TryConsumePellet(int x, int y)
        {
            if (grid[x, y] == '.')
            {
                grid[x, y] = ' ';
                PelletCount--;
                return true;
            }
            return false;
        }

        public char GetTile(int x, int y)
        {
            if (x < 0 || y < 0 || x >= Width || y >= Height) return '#';
            return grid[x, y];
        }
    }
}
