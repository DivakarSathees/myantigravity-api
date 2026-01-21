namespace ChessConsole
{
    public class King : Piece
    {
        public King(PieceColor color) : base(color) { }
        public override string WhiteSymbol => "♔";
        public override string BlackSymbol => "♚";
    }
}
