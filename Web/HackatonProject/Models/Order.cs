using System;
using System.Collections.Generic;

namespace HackatonProject.Models
{
    public class Order
    {
        public string? Id { get; set; }
        public string UserId { get; set; } = string.Empty;
        public DateTime OrderDate { get; set; } = DateTime.Now;
        public List<CartItem> Items { get; set; } = new();
        public decimal TotalAmount { get; set; }
        public string Address { get; set; } = string.Empty;
        public string Status { get; set; } = "Preparing"; // Preparing, Shipped, Delivered
    }
}
