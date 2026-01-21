namespace ChessApp
{
    public readonly struct Position
    {
        public int Rank { get; }
        public int File { get; }

        public Position(int rank, int file)
        {
            Rank = rank;
            File = file;
        }

        public override string ToString() => $"{(char)('a'+File)}{8-Rank}";
    }
}
