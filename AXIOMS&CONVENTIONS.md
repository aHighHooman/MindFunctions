# Naming
## Constants/Presets
- ALL_CAPS_LIKE_THIS
## Variables/Functions
- camelCaseLikeThis
## Classes
- CamelCaseLikeThis

# Composition Rules (Liekly no inheritance but compositions)
## Class Access Rules
- Each class may only directly access the data/function of its parent 
    - If a sibling's data/function is needed then move it up to the parent
    - If a grandfather's data is needed then move it down to the parent

## Init Structure
- Parent
    - Parent Inheritance
- Core Data / Features
- Children Declaration
