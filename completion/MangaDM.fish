function _manga_dm_completion;
    set -l cmd (commandline -opc | head -n 1 | string split " " | head -n 1)
    set -l response (env _MANGA_DM_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) $cmd);

    for completion in $response;
        set -l metadata (string split "," $completion);

        if test $metadata[1] = "dir";
            __fish_complete_directories $metadata[2];
        else if test $metadata[1] = "file";
            __fish_complete_path $metadata[2];
        else if test $metadata[1] = "plain";
            echo $metadata[2];
        end;
    end;
end;

complete --no-files --command manga-dm --arguments "(_manga_dm_completion)";
complete --no-files --command mangadm --arguments "(_manga_dm_completion)";
