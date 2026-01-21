namespace ChessConsole
{
    public class Bishop : Piece
    {
        public Bishop(PieceColor color) : base(color) { }
        public override string WhiteSymbol => "♗";
        public override string BlackSymbol => "♝";
    }
}
