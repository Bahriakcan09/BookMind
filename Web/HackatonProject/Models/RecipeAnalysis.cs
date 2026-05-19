using System.Collections.Generic;

namespace HackatonProject.Models
{
    public class RecipeAnalysisResult
    {
        public string RecipeName { get; set; } = string.Empty;
        public string PrepTime { get; set; } = string.Empty;
        public List<IngredientRequirement> Ingredients { get; set; } = new();
    }

    public class IngredientRequirement
    {
        public string Name { get; set; } = string.Empty;
        public double Amount { get; set; }
        public string Unit { get; set; } = string.Empty;
        public Product? MatchedProduct { get; set; }
    }
}
