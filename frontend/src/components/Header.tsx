
//Återanvändingsbar för alla Headers, men olika storlekar

type HeaderProps = {
    title: string
    size?: 'h1'|'h2'|'h3'|'h4'
}

export default function Header({title, size = 'h1'}: HeaderProps) {
    const sizeClasses: Record<string, string> = {
        h1: "text-4xl",
        h2: "text-3xl",
        h3: "text-2xl",
        h4: "text-xl",
    }
    //CSS i kodblocken tydligen emd tailwind?

    const selectedClass = sizeClasses[size] || sizeClasses.h1
     
    return (
        <h1 className={`${selectedClass} font-semibold text-gray-800 dark:text-white mb-6`}> {title} </h1>
    )
}