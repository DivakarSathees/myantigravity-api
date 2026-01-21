namespace ChessConsole
{
    public enum PieceColor
    {
        White,
        Black
    }

    public abstract class Piece
    {
        public PieceColor Color { get; }

        protected Piece(PieceColor color)
        {
            Color = color;
        }

        public abstract string WhiteSymbol { get; }
        public abstract string BlackSymbol { get; }

        public override string ToString() => Color == PieceColor.White ? WhiteSymbol : BlackSymbol;
    }
}
