using System.Collections.Generic;

namespace HackatonProject.Models
{
    public class CartItem
    {
        public string ProductId { get; set; } = string.Empty;
        public string ProductName { get; set; } = string.Empty;
        public decimal Price { get; set; }
        public int Quantity { get; set; }
        public string ImageUrl { get; set; } = string.Empty;
    }

    public class Cart
    {
        public string UserId { get; set; } = string.Empty;
        public List<CartItem> Items { get; set; } = new();
        public decimal TotalPrice => Items.Sum(i => i.Price * i.Quantity);
    }
}
