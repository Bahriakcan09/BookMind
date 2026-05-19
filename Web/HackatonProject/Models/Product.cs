namespace HackatonProject.Models
{
    public class Product
    {
        public string? Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public decimal Price { get; set; }
        public string Unit { get; set; } = string.Empty; // kg, adet, paket vb.
        public string Category { get; set; } = string.Empty;
        public string ImageUrl { get; set; } = string.Empty;
        public int StockQuantity { get; set; }
    }
}
