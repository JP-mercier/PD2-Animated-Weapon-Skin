-- Inversion Universal
--
-- Puts the animated material configs on the local player's own first-person weapon parts.
-- No base game file is overridden, so teammates, bots, enemies and lobby characters keep
-- their vanilla materials.

local MATERIALS_DIR = "units/mods/inversion_universal/materials/"
local IDS_MATERIAL_CONFIG = Idstring("material_config")

-- Vanilla material config -> animated replacement, keyed by Idstring key.
-- material_configs.txt lists the vanilla paths; each replacement is named after the last path segment.
local replacements = {}

for line in io.lines(ModPath .. "material_configs.txt") do
	local vanilla = line:match("^%s*(.-)%s*$")

	if vanilla ~= "" then
		replacements[Idstring(vanilla):key()] = Idstring(MATERIALS_DIR .. vanilla:match("[^/]+$"))
	end
end

local function replacement_for(part_data)
	-- Same default the vanilla code falls back to when it restores a part's material config.
	local vanilla = part_data.material_config or part_data.unit

	if type(vanilla) == "string" then
		vanilla = Idstring(vanilla)
	end

	return replacements[vanilla:key()]
end

Hooks:PostHook(NewRaycastWeaponBase, "_update_materials", "InversionUniversal_update_materials", function(self)
	-- NPC weapons are every third-person weapon (teammates, bots, lobby characters).
	-- VR renders the local weapon with third-person materials, and depth scaling would break it.
	if self:is_npc() or _G.IS_VR or not self._parts then
		return
	end

	for part_id, part in pairs(self._parts) do
		local part_data = managers.weapon_factory:get_part_data_by_part_id_from_weapon(part_id, self._factory_id, self._blueprint)
		local material_config = part_data and replacement_for(part_data)

		if material_config and alive(part.unit) and part.unit:material_config() ~= material_config and DB:has(IDS_MATERIAL_CONFIG, material_config) then
			part.unit:set_material_config(material_config, true)
		end
	end

	-- A skinned weapon has just collected the materials from its _cc configs, which were swapped out above.
	-- The animated materials have no skin layers, so leave nothing for the cosmetics code to paint.
	self._materials = nil
end)
