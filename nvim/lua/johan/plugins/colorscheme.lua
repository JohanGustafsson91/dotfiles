return {
	"oxfist/night-owl.nvim",
	lazy = false, -- make sure we load this during startup if it is your main colorscheme
	priority = 1000, -- make sure to load this before all the other start plugins
	config = function()
		local bg_visual = "#275378"
		local cursorline_bg = "#0e2a3f"

		-- load the colorscheme here
		require("night-owl").setup({
			transparent_background = true,
			on_colors = function(colors)
				colors.bg_visual = bg_visual
				colors.cursorline = cursorline_bg
			end,
		})
		vim.cmd.colorscheme("night-owl")
		vim.api.nvim_set_hl(0, "CursorLine", { bg = cursorline_bg })
	end,
}
