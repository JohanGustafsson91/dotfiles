return {
	"MeanderingProgrammer/render-markdown.nvim",
	dependencies = { "nvim-treesitter/nvim-treesitter", "nvim-tree/nvim-web-devicons" },
	ft = { "markdown" },
	opts = {
		-- Enable rendering by default
		enabled = true,
		-- Width of buffer (0 for full width)
		max_file_size = 10.0,
		-- Headings
		headings = { "󰲡 ", "󰲣 ", "󰲥 ", "󰲧 ", "󰲩 ", "󰲫 " },
		-- Code blocks
		code = {
			-- Turn on / off code block & inline code rendering
			enabled = true,
			-- Determines how code blocks are rendered
			style = "full",
			-- Width of the code block when not full width
			width = "block",
			-- Amount of padding to add around code blocks
			left_pad = 2,
			right_pad = 2,
		},
		-- Bullet points
		bullet = {
			-- Turn on / off list bullet rendering
			enabled = true,
			-- Replaces '-'|'+'|'*' of 'list_item'
			icons = { "●", "○", "◆", "◇" },
		},
	},
	config = function(_, opts)
		require("render-markdown").setup(opts)
	end,
}
