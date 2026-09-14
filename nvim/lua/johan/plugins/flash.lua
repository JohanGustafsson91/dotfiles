return {
	"folke/flash.nvim",
	event = "VeryLazy",
	opts = {
		modes = {
			-- Disable flash on regular f/t/F/T motions (keep them as default vim)
			char = { enabled = false },
		},
	},
	keys = {
		{ "s", function() require("flash").jump() vim.cmd("normal! zz") end, mode = { "n", "x", "o" }, desc = "Flash jump" },
		{ "S", function() require("flash").treesitter() vim.cmd("normal! zz") end, mode = { "n", "x", "o" }, desc = "Flash treesitter" },
	},
	config = function(_, opts)
		require("flash").setup(opts)
		-- Match night-owl color palette
		vim.api.nvim_set_hl(0, "FlashLabel", { bg = "#0e2a3f", fg = "#3EFFDC", bold = true })
		vim.api.nvim_set_hl(0, "FlashMatch", { bg = "#FFDA7B", fg = "#011627" })
		vim.api.nvim_set_hl(0, "FlashBackdrop", { fg = "#4b6479" })
	end,
}
