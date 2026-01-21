namespace ChessConsole
{
    public class Queen : Piece
    {
        public Queen(PieceColor color) : base(color) { }
        public override string WhiteSymbol => "♕";
        public override string BlackSymbol => "♛";
    }
}
