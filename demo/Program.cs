using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

// Simple console Pac-Man clone for .NET 6.0
// Controls: Arrow keys to move, Q to quit
// Build and run with: dotnet run

class Program
{
    static int Width = 28;
    static int Height = 15;

    static char Wall = '#';
    static char Pellet = '.';
    static char Empty = ' ';
    static char PlayerChar = 'C';
    static char GhostChar = 'G';

    static char[,] map;
    static (int x, int y) playerPos;
    static (int x, int y)[] ghostPos;
    static Random rnd = new Random();

    static int score = 0;
    static int lives = 3;
    static bool quitRequested = false;

    static void Main()
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;
        try
        {
            Console.CursorVisible = false;
            // optional: try to size console in supporting terminals
            try { Console.SetWindowSize(Math.Min(Width + 2, Console.LargestWindowWidth), Math.Min(Height + 5, Console.LargestWindowHeight)); } catch { }
        }
        catch { }

        InitializeMap();
        SpawnEntities();

        int frame = 0;
        DateTime lastMove = DateTime.UtcNow;
        TimeSpan moveInterval = TimeSpan.FromMilliseconds(120); // player movement frequency

        while (!quitRequested && lives > 0 && CountPellets() > 0)
        {
            var now = DateTime.UtcNow;
            // handle input (non-blocking)
            HandleInput();

            if (now - lastMove >= moveInterval)
            {
                UpdatePlayer();
                UpdateGhosts();
                CheckCollisions();
                lastMove = now;
            }

            Render();

            frame++;
            Thread.Sleep(10);
        }

        Render();
        Console.SetCursorPosition(0, Height + 2);
        if (lives <= 0)
            Console.WriteLine("Game Over! Final score: {0}", score);
        else if (CountPellets() == 0)
            Console.WriteLine("You win! Final score: {0}", score);
        else
            Console.WriteLine("Quit. Final score: {0}", score);

        Console.CursorVisible = true;
    }

    static void InitializeMap()
    {
        // A simple hard-coded map. # walls, . pellets, spaces empty
        string[] rows = new string[]
        {
            "############################",
            "#............##............#",
            "#.####.#####.##.#####.####.#",
            "#.#  #.#   #.##.#   #.#  #.#",
            "#.####.#####.##.#####.####.#",
            "#..........................#",
            "#.####.##.########.##.####.#",
            "#......##....##....##......#",
            "######.##### ## #####.######",
            "     #.##### ## #####.#     ",
            "######.##          ##.######",
            "#............##............#",
            "#.####.#####.##.#####.####.#",
            "#..........................#",
            "############################"
        };

        Height = rows.Length;
        Width = rows[0].Length;
        map = new char[Width, Height];

        for (int y = 0; y < Height; y++)
        {
            var line = rows[y];
            for (int x = 0; x < Width; x++)
            {
                char c = x < line.Length ? line[x] : ' ';
                if (c == ' ')
                    map[x, y] = Pellet; // open spaces contain pellets by default
                else if (c == '#')
                    map[x, y] = Wall;
                else
                    map[x, y] = c;

                // clear some spaces that should be blank (like tunnel area)
                if (map[x, y] == ' ') map[x, y] = Pellet;
            }
        }

        // turn explicit spaces into empty where intended (from map using space)
        for (int y = 0; y < Height; y++)
        for (int x = 0; x < Width; x++)
        {
            // the map above uses spaces for some voids; we want those to be empty
            if (rows[y][x] == ' ') map[x, y] = Empty;
        }

        // create a few power pellets
        var powerPellets = new (int x, int y)[] { (1, 1), (26, 1), (1, 13), (26, 13) };
        foreach (var p in powerPellets)
            if (map[p.x, p.y] != Wall) map[p.x, p.y] = Pellet;
    }

    static void SpawnEntities()
    {
        playerPos = (14, 11);
        ghostPos = new (int x, int y)[3];
        ghostPos[0] = (13, 7);
        ghostPos[1] = (14, 7);
        ghostPos[2] = (15, 7);
    }

    static void HandleInput()
    {
        while (Console.KeyAvailable)
        {
            var key = Console.ReadKey(true);
            if (key.Key == ConsoleKey.Q)
            {
                quitRequested = true;
                return;
            }

            // store a desired move on key press in a temp variable
            // we will attempt to move on the next UpdatePlayer call
            switch (key.Key)
            {
                case ConsoleKey.UpArrow: desiredMove = (0, -1); break;
                case ConsoleKey.DownArrow: desiredMove = (0, 1); break;
                case ConsoleKey.LeftArrow: desiredMove = (-1, 0); break;
                case ConsoleKey.RightArrow: desiredMove = (1, 0); break;
            }
        }
    }

    static (int dx, int dy) desiredMove = (0, 0);

    static void UpdatePlayer()
    {
        if (desiredMove == (0, 0)) return;

        var newPos = (x: playerPos.x + desiredMove.dx, y: playerPos.y + desiredMove.dy);
        if (IsWalkable(newPos.x, newPos.y))
        {
            playerPos = newPos;
            if (map[playerPos.x, playerPos.y] == Pellet)
            {
                score += 10;
                map[playerPos.x, playerPos.y] = Empty;
                try { Console.Beep(800, 40); } catch { }
            }
        }

        // reset desired move to avoid continuous movement in the same direction unless key held
        desiredMove = (0, 0);
    }

    static void UpdateGhosts()
    {
        for (int i = 0; i < ghostPos.Length; i++)
        {
            var g = ghostPos[i];
            // pick a random direction that is walkable (prefers directions that move toward player slightly)
            var dirs = new List<(int dx, int dy)>() { (0, -1), (0, 1), (-1, 0), (1, 0) };

            // sort by closeness to player (biased)
            dirs = dirs.OrderBy(d => rnd.Next(3) + Distance((g.x + d.dx, g.y + d.dy), playerPos)).ToList();

            foreach (var d in dirs)
            {
                int nx = g.x + d.dx, ny = g.y + d.dy;
                if (IsWalkable(nx, ny) && !IsGhostAt(nx, ny))
                {
                    ghostPos[i] = (nx, ny);
                    break;
                }
            }
        }
    }

    static int Distance((int x, int y) a, (int x, int y) b)
    {
        return Math.Abs(a.x - b.x) + Math.Abs(a.y - b.y);
    }

    static bool IsWalkable(int x, int y)
    {
        if (x < 0 || x >= Width || y < 0 || y >= Height) return false;
        return map[x, y] != Wall;
    }

    static bool IsGhostAt(int x, int y)
    {
        for (int i = 0; i < ghostPos.Length; i++) if (ghostPos[i].x == x && ghostPos[i].y == y) return true;
        return false;
    }

    static void CheckCollisions()
    {
        for (int i = 0; i < ghostPos.Length; i++)
        {
            if (ghostPos[i].x == playerPos.x && ghostPos[i].y == playerPos.y)
            {
                // collision
                lives--;
                try { Console.Beep(300, 200); } catch { }
                // reset positions
                playerPos = (14, 11);
                ghostPos[0] = (13, 7);
                ghostPos[1] = (14, 7);
                ghostPos[2] = (15, 7);
                Thread.Sleep(500);
                break;
            }
        }
    }

    static int CountPellets()
    {
        int count = 0;
        for (int y = 0; y < Height; y++)
            for (int x = 0; x < Width; x++)
                if (map[x, y] == Pellet) count++;
        return count;
    }

    static void Render()
    {
        // draw map and entities
        int top = 0;
        for (int y = 0; y < Height; y++)
        {
            Console.SetCursorPosition(0, top + y);
            for (int x = 0; x < Width; x++)
            {
                if (playerPos.x == x && playerPos.y == y)
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.Write(PlayerChar);
                }
                else if (IsGhostAt(x, y))
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.Write(GhostChar);
                }
                else
                {
                    var c = map[x, y];
                    if (c == Wall)
                    {
                        Console.ForegroundColor = ConsoleColor.Blue;
                        Console.Write('█');
                    }
                    else if (c == Pellet)
                    {
                        Console.ForegroundColor = ConsoleColor.DarkYellow;
                        Console.Write('.');
                    }
                    else
                    {
                        Console.Write(' ');
                    }
                }
            }
            Console.ResetColor();
        }

        // HUD
        Console.SetCursorPosition(0, Height + 1);
        Console.Write($"Score: {score}   Lives: {lives}   Pellets left: {CountPellets()}   (Use arrow keys, Q to quit)        ");
    }
}
